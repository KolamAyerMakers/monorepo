"""Create initial state tables."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260529_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the initial SQLite state schema."""
    for statement in _CREATE_TABLE_STATEMENTS:
        alembic_operations.execute(statement)
    for statement in _CREATE_INDEX_STATEMENTS:
        alembic_operations.execute(statement)


def downgrade() -> None:
    """Drop the initial SQLite state schema."""
    for statement in _DROP_TABLE_STATEMENTS:
        alembic_operations.execute(statement)


_TABLE_NAMES = (
    "outbox_items",
    "audit_events",
    "projection_versions",
    "command_observations",
    "help_interactions",
    "group_grants",
    "tier_promotions",
    "score_ledger",
    "quest_completions",
    "quest_attempts",
    "quest_instances",
    "quest_assignments",
    "cohort_memberships",
    "learners",
)

_DROP_TABLE_STATEMENTS = tuple(f"drop table {table_name}" for table_name in _TABLE_NAMES)

_CREATE_TABLE_STATEMENTS = (
    """
    create table learners (
        handle text primary key,
        joined_at text not null,
        tagline text null,
        created_at text not null
    )
    """,
    """
    create table cohort_memberships (
        handle text not null references learners(handle) on delete cascade,
        course_id text not null,
        joined_at text not null,
        session_reached text null,
        primary key (handle, course_id)
    )
    """,
    """
    create table quest_assignments (
        id integer primary key,
        handle text not null references learners(handle) on delete cascade,
        course_id text not null,
        quest_id text not null,
        assigned_at text not null,
        source text not null,
        unique (handle, course_id, quest_id)
    )
    """,
    """
    create table quest_instances (
        handle text not null references learners(handle) on delete cascade,
        course_id text not null,
        quest_id text not null,
        seed text not null,
        generated_at text not null,
        expected_answer_hash text null,
        data_json text not null,
        primary key (handle, course_id, quest_id)
    )
    """,
    """
    create table quest_attempts (
        id integer primary key,
        handle text not null references learners(handle) on delete cascade,
        course_id text not null,
        quest_id text not null,
        attempted_at text not null,
        source text not null,
        outcome text not null,
        failure_reason text null,
        evidence_json text not null
    )
    """,
    """
    create table quest_completions (
        handle text not null references learners(handle) on delete cascade,
        course_id text not null,
        quest_id text not null,
        attempt_id integer null references quest_attempts(id) on delete set null,
        completed_at text not null,
        source text not null,
        primary key (handle, course_id, quest_id)
    )
    """,
    """
    create table score_ledger (
        id integer primary key,
        handle text not null references learners(handle) on delete cascade,
        course_id text not null,
        amount integer not null,
        reason text not null,
        related_type text null,
        related_id text null,
        created_at text not null,
        check (
            reason != 'quest_completed'
            or coalesce(related_type = 'quest' and related_id is not null, 0)
        )
    )
    """,
    """
    create table tier_promotions (
        handle text not null references learners(handle) on delete cascade,
        course_id text not null,
        tier_id text not null,
        promoted_at text not null,
        score_total integer not null,
        primary key (handle, course_id, tier_id)
    )
    """,
    """
    create table group_grants (
        handle text not null references learners(handle) on delete cascade,
        group_name text not null,
        intended_state text not null,
        reason text not null,
        updated_at text not null,
        primary key (handle, group_name)
    )
    """,
    """
    create table help_interactions (
        id integer primary key,
        handle text not null references learners(handle) on delete cascade,
        source text not null,
        visibility text not null,
        question text not null,
        response text null,
        topic_tags text not null,
        created_at text not null,
        answered_at text null
    )
    """,
    """
    create table command_observations (
        id integer primary key,
        handle text not null references learners(handle) on delete cascade,
        course_id text not null,
        command text not null,
        cwd text not null,
        phase text not null,
        exit_status integer null,
        observed_at text not null
    )
    """,
    """
    create table projection_versions (
        name text primary key,
        last_written_at text not null,
        version integer not null
    )
    """,
    """
    create table audit_events (
        id integer primary key,
        event_type text not null,
        handle text null references learners(handle) on delete set null,
        source text not null,
        created_at text not null,
        payload_json text not null,
        exported_at text null
    )
    """,
    """
    create table outbox_items (
        id integer primary key,
        kind text not null,
        status text not null,
        created_at text not null,
        processed_at text null,
        payload_json text not null
    )
    """,
)

_CREATE_INDEX_STATEMENTS = (
    "create index quest_attempts_lookup on quest_attempts (handle, course_id, quest_id)",
    "create index score_ledger_lookup on score_ledger (handle, course_id, created_at)",
    (
        "create unique index score_ledger_unique_quest_completion "
        "on score_ledger (handle, course_id, related_id) "
        "where reason = 'quest_completed' "
        "and related_type = 'quest' "
        "and related_id is not null"
    ),
    "create index help_interactions_handle_created on help_interactions (handle, created_at)",
    (
        "create index command_observations_handle_course_observed "
        "on command_observations (handle, course_id, observed_at)"
    ),
    "create index audit_events_exported on audit_events (exported_at, id)",
    "create index outbox_items_status_created on outbox_items (status, created_at)",
    """
    create trigger quest_attempts_are_append_only
    before update on quest_attempts
    begin
        select raise(abort, 'quest attempts are append-only');
    end
    """,
    """
    create trigger quest_completions_insert_attempt_must_match
    before insert on quest_completions
    when new.attempt_id is not null
        and not exists (
            select 1
            from quest_attempts
            where id = new.attempt_id
                and handle = new.handle
                and course_id = new.course_id
                and quest_id = new.quest_id
                and outcome = 'passed'
        )
    begin
        select raise(abort, 'quest completion attempt must match passed quest attempt');
    end
    """,
    """
    create trigger quest_completions_update_attempt_must_match
    before update on quest_completions
    when new.attempt_id is not null
        and not exists (
            select 1
            from quest_attempts
            where id = new.attempt_id
                and handle = new.handle
                and course_id = new.course_id
                and quest_id = new.quest_id
                and outcome = 'passed'
        )
    begin
        select raise(abort, 'quest completion attempt must match passed quest attempt');
    end
    """,
)
