"""Tests for Alembic migration setup."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import cast

import pytest

from maker_guide.repositories.helpers import DATABASE_FILE_MODE
from tests.conftest import PROJECT_ROOT, run_alembic

EXPECTED_STATE_TABLES = frozenset(
    {
        "learners",
        "cohort_memberships",
        "course_releases",
        "quest_assignments",
        "quest_instances",
        "quest_attempts",
        "quest_completions",
        "score_ledger",
        "tier_promotions",
        "group_grants",
        "help_interactions",
        "command_observations",
        "projection_versions",
        "audit_events",
        "llm_audit_logs",
        "session_objective_completions",
        "peer_thanks",
        "outbox_items",
    },
)


def test_migrations_create_initial_state_tables(migrated_database_path: Path) -> None:
    """Alembic migrations create the initial SQLite state schema."""
    with sqlite3.connect(migrated_database_path) as database_connection:
        table_name_rows = cast(
            "list[tuple[str]]",
            database_connection.execute(
                "select name from sqlite_master where type = 'table'",
            ).fetchall(),
        )
        table_names = {table_name for (table_name,) in table_name_rows}

    assert table_names == EXPECTED_STATE_TABLES | {"alembic_version"}


def test_alembic_current_reports_latest_revision(temporary_path: Path) -> None:
    """The Alembic CLI can report the migrated revision."""
    database_path = temporary_path / "state.db"
    run_alembic(database_path, "upgrade", "head")

    assert "20260801_0016" in run_alembic(database_path, "current").stdout


def test_rank_eligibility_migration_defaults_existing_memberships_to_true(
    temporary_path: Path,
) -> None:
    """Existing cohort memberships remain eligible after the schema upgrade."""
    database_path = temporary_path / "state.db"
    run_alembic(database_path, "upgrade", "20260718_0014")
    with sqlite3.connect(database_path) as database_connection:
        database_connection.execute(
            """insert into learners (handle, joined_at, tagline, created_at)
            values ('alice', '2026-07-18T09:00:00Z', null, '2026-07-18T09:00:00Z')""",
        )
        database_connection.execute(
            """insert into cohort_memberships (handle, course_id, joined_at)
            values ('alice', 'lf2607', '2026-07-18T09:00:00Z')""",
        )

    run_alembic(database_path, "upgrade", "head")

    with sqlite3.connect(database_path) as database_connection:
        assert database_connection.execute(
            "select rank_eligible from cohort_memberships where handle = 'alice'",
        ).fetchone() == (1,)


def test_s3_child_objective_migration_copies_progress_and_scores(
    temporary_path: Path,
) -> None:
    """Split S3 objectives inherit parent evidence and standard score awards."""
    database_path = temporary_path / "state.db"
    run_alembic(database_path, "upgrade", "20260719_0015")
    parent_completions = (
        ("make-first-pipe", "2026-07-19T09:00:00Z", '{"proof":"pipe"}'),
        ("combine-and-copy-streams", "2026-07-19T09:01:00Z", '{"proof":"streams"}'),
        ("read-process-table", "2026-07-19T09:02:00Z", '{"proof":"processes"}'),
    )
    with sqlite3.connect(database_path) as database_connection:
        database_connection.execute(
            """insert into learners (handle, joined_at, tagline, created_at)
            values ('alice', '2026-07-18T09:00:00Z', null, '2026-07-18T09:00:00Z')""",
        )
        database_connection.execute(
            """insert into cohort_memberships (handle, course_id, joined_at)
            values ('alice', 'lf2607', '2026-07-18T09:00:00Z')""",
        )
        database_connection.executemany(
            """insert into session_objective_completions
            (handle, course_id, session_id, objective_id, completed_at, evidence_json)
            values ('alice', 'lf2607', 'S3', ?, ?, ?)""",
            parent_completions,
        )
        database_connection.execute(
            """insert into session_objective_completions
            (handle, course_id, session_id, objective_id, completed_at, evidence_json)
            values ('alice', 'lf2607', 'S3', 'unrelated', '2026-07-19T09:03:00Z', '{}')""",
        )

    run_alembic(database_path, "upgrade", "head")

    with sqlite3.connect(database_path) as database_connection:
        assert database_connection.execute(
            """select objective_id, completed_at, evidence_json
            from session_objective_completions
            where objective_id not in (
                'make-first-pipe', 'combine-and-copy-streams', 'read-process-table', 'unrelated'
            )
            order by objective_id""",
        ).fetchall() == [
            ("describe-running-process", "2026-07-19T09:02:00Z", '{"proof":"processes"}'),
            ("name-stdin-descriptor", "2026-07-19T09:00:00Z", '{"proof":"pipe"}'),
            ("name-stdout-descriptor", "2026-07-19T09:00:00Z", '{"proof":"pipe"}'),
            ("read-redirections-left-to-right", "2026-07-19T09:01:00Z", '{"proof":"streams"}'),
            ("report-process-pair", "2026-07-19T09:02:00Z", '{"proof":"processes"}'),
            (
                "route-stderr-to-stdout-destination",
                "2026-07-19T09:01:00Z",
                '{"proof":"streams"}',
            ),
        ]
        assert database_connection.execute(
            """select amount, related_id, created_at
            from score_ledger
            order by related_id""",
        ).fetchall() == [
            (50, "S3:describe-running-process", "2026-07-19T09:02:00Z"),
            (50, "S3:name-stdin-descriptor", "2026-07-19T09:00:00Z"),
            (50, "S3:name-stdout-descriptor", "2026-07-19T09:00:00Z"),
            (50, "S3:read-redirections-left-to-right", "2026-07-19T09:01:00Z"),
            (50, "S3:report-process-pair", "2026-07-19T09:02:00Z"),
            (50, "S3:route-stderr-to-stdout-destination", "2026-07-19T09:01:00Z"),
        ]

    run_alembic(database_path, "downgrade", "20260719_0015")

    with sqlite3.connect(database_path) as database_connection:
        assert database_connection.execute(
            """select objective_id from session_objective_completions order by objective_id""",
        ).fetchall() == [
            ("combine-and-copy-streams",),
            ("make-first-pipe",),
            ("read-process-table",),
            ("unrelated",),
        ]
        assert database_connection.execute("select count(*) from score_ledger").fetchone() == (0,)


def test_quest_id_rename_preserves_existing_progress(temporary_path: Path) -> None:
    """Renaming the quest keeps its learner state and scores connected."""
    database_path = temporary_path / "state.db"
    run_alembic(database_path, "upgrade", "20260717_0013")
    with sqlite3.connect(database_path) as database_connection:
        database_connection.execute(
            """insert into learners (handle, joined_at, tagline, created_at)
            values ('alice', '2026-07-18T09:00:00Z', null, '2026-07-18T09:00:00Z')""",
        )
        database_connection.execute(
            """insert into cohort_memberships (handle, course_id, joined_at)
            values ('alice', 'lf2607', '2026-07-18T09:00:00Z')""",
        )
        database_connection.execute(
            """insert into quest_assignments
            (handle, course_id, quest_id, assigned_at, source)
            values ('alice', 'lf2607', 'read-man-ls', '2026-07-18T09:00:00Z', 'test')""",
        )
        database_connection.execute(
            """insert into quest_instances
            (handle, course_id, quest_id, seed, generated_at, expected_answer_hash, data_json)
            values (
                'alice', 'lf2607', 'read-man-ls', 'seed', '2026-07-18T09:00:00Z', null, '{}'
            )""",
        )
        database_connection.execute(
            """insert into quest_attempts
            (
                handle, course_id, quest_id, attempted_at, source, outcome, failure_reason,
                evidence_json
            )
            values (
                'alice', 'lf2607', 'read-man-ls', '2026-07-18T09:00:00Z', 'test', 'passed', null,
                '{}'
            )""",
        )
        database_connection.execute(
            """insert into quest_completions
            (handle, course_id, quest_id, attempt_id, completed_at, source)
            values ('alice', 'lf2607', 'read-man-ls', 1, '2026-07-18T09:00:00Z', 'test')""",
        )
        database_connection.executemany(
            """insert into score_ledger
            (handle, course_id, amount, reason, related_type, related_id, created_at)
            values ('alice', 'lf2607', 25, ?, 'quest', 'read-man-ls', '2026-07-18T09:00:00Z')""",
            [("quest_completed",), ("quest_completion_speed_bonus",)],
        )

    run_alembic(database_path, "upgrade", "head")

    with sqlite3.connect(database_path) as database_connection:
        assert (
            database_connection.execute(
                """select quest_id from quest_assignments where handle = 'alice'
            union all select quest_id from quest_instances where handle = 'alice'
            union all select quest_id from quest_attempts where handle = 'alice'
            union all select quest_id from quest_completions where handle = 'alice'""",
            ).fetchall()
            == [("explain-ls",)] * 4
        )
        assert database_connection.execute(
            """select related_id from score_ledger where handle = 'alice'
            order by reason""",
        ).fetchall() == [("explain-ls",), ("explain-ls",)]
        with pytest.raises(sqlite3.IntegrityError, match="quest attempts are append-only"):
            database_connection.execute("update quest_attempts set outcome = 'failed' where id = 1")


def test_peer_thank_score_migration_backfills_existing_thanks(temporary_path: Path) -> None:
    """Existing thank-you records receive one visible score award each."""
    database_path = temporary_path / "state.db"
    run_alembic(database_path, "upgrade", "20260717_0006")
    with sqlite3.connect(database_path) as database_connection:
        database_connection.execute(
            """
            insert into learners (handle, joined_at, tagline, created_at)
            values ('alice', '2026-07-17T01:00:00Z', null, '2026-07-17T01:00:00Z')
            """,
        )
        database_connection.execute(
            """
            insert into learners (handle, joined_at, tagline, created_at)
            values ('bob', '2026-07-17T01:00:00Z', null, '2026-07-17T01:00:00Z')
            """,
        )
        for handle in ("alice", "bob"):
            database_connection.execute(
                """
                insert into cohort_memberships (handle, course_id, joined_at, session_reached)
                values (?, 'lf2607', '2026-07-17T01:00:00Z', 'S1')
                """,
                (handle,),
            )
        database_connection.execute(
            """
            insert into peer_thanks
                (giver_handle, recipient_handle, course_id, reason, thanked_on, created_at)
            values (
                'alice', 'bob', 'lf2607', 'Explained SSH permissions',
                '2026-07-17', '2026-07-17T01:53:20Z'
            )
            """,
        )

    run_alembic(database_path, "upgrade", "head")

    with sqlite3.connect(database_path) as database_connection:
        assert database_connection.execute(
            """
            select handle, course_id, amount, reason, related_type, related_id, created_at
            from score_ledger
            """,
        ).fetchall() == [
            (
                "bob",
                "lf2607",
                10,
                "peer_thank_received",
                "peer_thank",
                "1",
                "2026-07-17T01:53:20Z",
            ),
        ]


def test_course_rename_migration_updates_persisted_course_ids(temporary_path: Path) -> None:
    """The lf2607 course rename updates existing learner state."""
    database_path = temporary_path / "state.db"
    run_alembic(database_path, "upgrade", "20260610_0002")
    with sqlite3.connect(database_path) as database_connection:
        database_connection.execute(
            """
            insert into learners (handle, joined_at, tagline, created_at)
            values ('alice', '2026-07-04T14:04:37Z', null, '2026-07-04T14:04:37Z')
            """,
        )
        database_connection.execute(
            """
            insert into cohort_memberships (handle, course_id, joined_at, session_reached)
            values ('alice', 'linux-foundations-2026-07', '2026-07-04T14:04:37Z', 'S1')
            """,
        )
        database_connection.execute(
            """
            insert into group_grants (handle, group_name, intended_state, reason, updated_at)
            values (
                'alice',
                'linux-foundations-2026-07',
                'present',
                'course:linux-foundations-2026-07',
                '2026-07-04T14:04:37Z'
            )
            """,
        )
        database_connection.execute(
            """
            insert into quest_attempts (
                handle,
                course_id,
                quest_id,
                attempted_at,
                source,
                outcome,
                failure_reason,
                evidence_json
            )
            values (
                'alice',
                'linux-foundations-2026-07',
                'quest-1',
                '2026-07-04T14:04:37Z',
                'test',
                'failed',
                null,
                '{}'
            )
            """,
        )

    run_alembic(database_path, "upgrade", "head")

    with sqlite3.connect(database_path) as database_connection:
        assert database_connection.execute(
            "select course_id from cohort_memberships where handle = 'alice'",
        ).fetchall() == [("lf2607",)]
        assert database_connection.execute(
            "select group_name, reason from group_grants where handle = 'alice'",
        ).fetchall() == [("lf2607", "course:lf2607")]
        assert database_connection.execute(
            "select course_id from quest_attempts where handle = 'alice'",
        ).fetchall() == [("lf2607",)]


def test_course_release_migration_requires_an_explicit_release(temporary_path: Path) -> None:
    """Existing individual placement does not silently release course material."""
    database_path = temporary_path / "state.db"
    run_alembic(database_path, "upgrade", "20260717_0009")
    with sqlite3.connect(database_path) as database_connection:
        database_connection.execute(
            """insert into learners (handle, joined_at, tagline, created_at)
            values ('alice', '2026-07-17T01:00:00Z', null, '2026-07-17T01:00:00Z')""",
        )
        database_connection.execute(
            """insert into cohort_memberships (handle, course_id, joined_at, session_reached)
            values ('alice', 'lf2607', '2026-07-17T01:00:00Z', 'S2')""",
        )

    run_alembic(database_path, "upgrade", "head")

    with sqlite3.connect(database_path) as database_connection:
        assert (
            database_connection.execute(
                "select course_id, session_reached from course_releases",
            ).fetchall()
            == []
        )
        column_records = cast(
            "list[tuple[int, str, str, int, object, int]]",
            database_connection.execute("pragma table_info(cohort_memberships)").fetchall(),
        )
        assert "session_reached" not in {column_record[1] for column_record in column_records}


def test_alembic_migrations_create_group_readable_state_file(temporary_path: Path) -> None:
    """Migration-created SQLite files are readable by the deployment group."""
    database_path = temporary_path / "state.db"
    previous_umask = os.umask(0)
    try:
        run_alembic(database_path, "upgrade", "head")
    finally:
        os.umask(previous_umask)

    assert database_path.stat().st_mode & 0o777 == DATABASE_FILE_MODE


def test_alembic_history_lists_initial_revision(temporary_path: Path) -> None:
    """The Alembic CLI lists the hand-written migration."""
    history_stdout = run_alembic(temporary_path / "state.db", "history").stdout

    assert "20260529_0001" in history_stdout


def test_application_code_does_not_import_sqlalchemy() -> None:
    """SQLAlchemy is migration plumbing only, not an application dependency."""
    for source_path in (PROJECT_ROOT / "src" / "maker_guide").rglob("*.py"):
        if "migrations" in source_path.parts:
            continue
        assert "sqlalchemy" not in source_path.read_text(encoding="utf-8").lower()
