"""Tests for score ledger repository functions."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from maker_guide.repositories.helpers import RepositoryError, connect_database
from maker_guide.repositories.learner import get_learner, upsert_learner
from maker_guide.repositories.score_ledger import (
    ScoreLedgerEntry,
    add_score_entry,
    list_score_entries,
    total_score_for_course,
)
from tests.repositories.helpers import COURSE_ID, TIMESTAMP, learner


def test_score_ledger_entries_sum_course_total(migrated_database_path: Path) -> None:
    """Score ledger entries are append-only and summed by course."""
    with connect_database(migrated_database_path) as database_connection:
        upsert_learner(database_connection, learner())
        add_score_entry(
            database_connection,
            _score_entry(amount=25, related_id="prove-shell-alive"),
        )
        add_score_entry(database_connection, _score_entry(amount=75, related_id="name-system"))

        assert total_score_for_course(database_connection, "alice", COURSE_ID) == 100
        assert [
            entry.related_id
            for entry in list_score_entries(database_connection, "alice", COURSE_ID)
        ] == [
            "prove-shell-alive",
            "name-system",
        ]


def test_quest_completion_score_is_idempotent(migrated_database_path: Path) -> None:
    """Retrying the same quest score award does not duplicate learner progress."""
    with connect_database(migrated_database_path) as database_connection:
        upsert_learner(database_connection, learner())

        first_entry_id = add_score_entry(
            database_connection,
            _score_entry(amount=25, related_id="prove-shell-alive"),
        )
        second_entry_id = add_score_entry(
            database_connection,
            _score_entry(amount=25, related_id="prove-shell-alive"),
        )

        assert second_entry_id == first_entry_id
        assert total_score_for_course(database_connection, "alice", COURSE_ID) == 25
        assert len(list_score_entries(database_connection, "alice", COURSE_ID)) == 1


def test_quest_completion_score_rejects_conflicting_retry(migrated_database_path: Path) -> None:
    """Retrying a quest score award with a different amount is a service bug."""
    with connect_database(migrated_database_path) as database_connection:
        upsert_learner(database_connection, learner())
        add_score_entry(
            database_connection,
            _score_entry(amount=25, related_id="prove-shell-alive"),
        )

        with pytest.raises(RepositoryError, match="conflicting score ledger entry"):
            add_score_entry(
                database_connection,
                _score_entry(amount=50, related_id="prove-shell-alive"),
            )


def test_quest_completion_score_requires_related_quest_id(migrated_database_path: Path) -> None:
    """Quest completion score must identify the quest that caused the award."""
    with connect_database(migrated_database_path) as database_connection:
        upsert_learner(database_connection, learner())

        with pytest.raises(RepositoryError, match="quest completion score requires"):
            add_score_entry(database_connection, _score_entry(amount=25, related_id=None))


def test_quest_completion_score_schema_requires_related_quest_id(
    migrated_database_path: Path,
) -> None:
    """The SQLite schema rejects malformed quest-completion score rows."""
    with connect_database(migrated_database_path) as database_connection:
        upsert_learner(database_connection, learner())

        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            database_connection.execute(
                """
                insert into score_ledger
                    (handle, course_id, amount, reason, related_type, related_id, created_at)
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                ("alice", COURSE_ID, 25, "quest_completed", "quest", None, TIMESTAMP),
            )


def test_quest_speed_bonus_requires_completed_quest(migrated_database_path: Path) -> None:
    """The SQLite guard rejects a bonus without a completed quest."""
    with connect_database(migrated_database_path) as database_connection:
        upsert_learner(database_connection, learner())

        with pytest.raises(sqlite3.IntegrityError, match="quest speed bonus requires"):
            add_score_entry(
                database_connection,
                ScoreLedgerEntry(
                    id=None,
                    handle="alice",
                    course_id=COURSE_ID,
                    amount=3,
                    reason="quest_completion_speed_bonus",
                    related_type="quest",
                    related_id="prove-shell-alive",
                    created_at=TIMESTAMP,
                ),
            )


def test_service_transaction_rolls_back_repository_writes(migrated_database_path: Path) -> None:
    """Service-owned transactions roll back repository writes together."""
    with connect_database(migrated_database_path) as database_connection:
        with pytest.raises(RuntimeError, match="service failed"):
            _write_then_fail(database_connection)

        assert get_learner(database_connection, "alice") is None
        assert total_score_for_course(database_connection, "alice", COURSE_ID) == 0


def _write_then_fail(database_connection: sqlite3.Connection) -> None:
    with database_connection:
        upsert_learner(database_connection, learner(tagline="temporary"))
        add_score_entry(
            database_connection,
            _score_entry(amount=100, related_id="prove-shell-alive"),
        )
        raise RuntimeError("service failed")


def _score_entry(amount: int, related_id: str | None) -> ScoreLedgerEntry:
    return ScoreLedgerEntry(
        id=None,
        handle="alice",
        course_id=COURSE_ID,
        amount=amount,
        reason="quest_completed",
        related_type="quest",
        related_id=related_id,
        created_at=TIMESTAMP,
    )
