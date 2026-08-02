"""Award session objective scores and first-completion bonuses."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260717_0009"
down_revision: str | None = "20260717_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add objective score integrity and ranking query support."""
    for statement in _CREATE_STATEMENTS:
        alembic_operations.execute(statement)


def downgrade() -> None:
    """Remove objective score guards without revoking awards."""
    for statement in _DROP_STATEMENTS:
        alembic_operations.execute(statement)


_CREATE_STATEMENTS = (
    """create index session_objective_completions_course_objective
    on session_objective_completions (course_id, session_id, objective_id)""",
    """create unique index score_ledger_unique_session_objective_completed
    on score_ledger (handle, course_id, related_id)
    where reason = 'session_objective_completed'
        and related_type = 'session_objective'
        and related_id is not null""",
    """create unique index score_ledger_unique_session_objective_speed_bonus
    on score_ledger (handle, course_id, related_id)
    where reason = 'session_objective_speed_bonus'
        and related_type = 'session_objective'
        and related_id is not null""",
    """create trigger score_ledger_session_objective_score_source
    before insert on score_ledger
    when new.reason in ('session_objective_completed', 'session_objective_speed_bonus')
        and not exists (
            select 1
            from session_objective_completions
            where handle = new.handle
                and course_id = new.course_id
                and session_id || ':' || objective_id = new.related_id
        )
    begin
        select raise(abort, 'session objective score requires its completed objective');
    end""",
)

_DROP_STATEMENTS = (
    "drop trigger score_ledger_session_objective_score_source",
    "drop index score_ledger_unique_session_objective_speed_bonus",
    "drop index score_ledger_unique_session_objective_completed",
    "drop index session_objective_completions_course_objective",
)
