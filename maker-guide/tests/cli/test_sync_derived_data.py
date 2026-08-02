"""Tests for derived data synchronization CLI."""

from __future__ import annotations

import fcntl
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from maker_guide.cli.sync_derived_data import run
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.repositories.cohort_membership import CohortMembership, upsert_membership
from maker_guide.repositories.course_release import CourseRelease, upsert_course_release
from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.learner import Learner, upsert_learner
from maker_guide.repositories.score_ledger import ScoreLedgerEntry, add_score_entry


def test_sync_derived_data_cli_projects_makers_from_database(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """The CLI rebuilds `/makers` from the configured SQLite database."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle="alice",
                course_id=CATALOG.course.id,
                amount=500,
                reason="quest_completed",
                related_type="quest",
                related_id="prove-shell-alive",
                created_at="2026-07-19T09:00:00Z",
            ),
        )

    makers_root = temporary_path / "makers"
    documents_root = temporary_path / "docs"

    assert (
        run(
            [
                "--database",
                str(migrated_database_path),
                "--makers-root",
                str(makers_root),
                "--documents-root",
                str(documents_root),
            ],
        )
        == 0
    )
    assert (makers_root / "alice" / "rank").read_text(encoding="utf-8") == "1\n"
    assert (makers_root / "alice" / "score").read_text(encoding="utf-8") == "500\n"
    assert (makers_root / "alice" / "tier").read_text(encoding="utf-8") == "apprentice\n"
    assert (documents_root / "quests" / "prove-shell-alive.md").exists()


def test_sync_derived_data_cli_rejects_concurrent_sync(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """The CLI fails without writing files when the makers-root lock is held."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle="alice",
                course_id=CATALOG.course.id,
                amount=100,
                reason="quest_completed",
                related_type="quest",
                related_id="prove-shell-alive",
                created_at="2026-07-19T09:00:00Z",
            ),
        )

    makers_root = temporary_path / "makers"
    documents_root = temporary_path / "docs"
    makers_root.mkdir()
    with _held_sync_lock(makers_root):
        assert (
            run(
                [
                    "--database",
                    str(migrated_database_path),
                    "--makers-root",
                    str(makers_root),
                    "--documents-root",
                    str(documents_root),
                ],
            )
            == 1
        )

    assert not (makers_root / "alice").exists()
    assert (
        run(
            [
                "--database",
                str(migrated_database_path),
                "--makers-root",
                str(makers_root),
                "--documents-root",
                str(documents_root),
            ],
        )
        == 0
    )
    assert (makers_root / "alice" / "rank").read_text(encoding="utf-8") == "1\n"


def test_sync_derived_data_cli_rejects_unknown_course_id(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """The CLI selects catalogs through the composition root."""
    assert (
        run(
            [
                "--database",
                str(migrated_database_path),
                "--makers-root",
                str(temporary_path / "makers"),
                "--course-id",
                "missing-course",
            ],
        )
        == 1
    )


def _write_member(database_connection: sqlite3.Connection) -> None:
    upsert_learner(
        database_connection,
        Learner(
            handle="alice",
            joined_at="2026-07-18T09:00:00Z",
            tagline=None,
            created_at="2026-07-18T09:00:00Z",
        ),
    )
    upsert_membership(
        database_connection,
        CohortMembership(
            handle="alice",
            course_id=CATALOG.course.id,
            joined_at="2026-07-18T09:00:00Z",
        ),
    )
    upsert_course_release(
        database_connection,
        CourseRelease(
            course_id=CATALOG.course.id,
            session_reached="S1",
            released_at="2026-07-18T09:00:00Z",
        ),
    )


@contextmanager
def _held_sync_lock(makers_root: Path) -> Generator[None]:
    with (makers_root / ".sync.lock").open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
