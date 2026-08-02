"""Tests for quest completion repository functions."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from maker_guide.repositories.helpers import RepositoryError, connect_database
from maker_guide.repositories.quest_attempt import QuestAttempt, record_quest_attempt
from maker_guide.repositories.quest_completion import (
    QuestCompletion,
    complete_quest,
    get_quest_completion,
)
from tests.repositories.helpers import COURSE_ID, TIMESTAMP, write_learner


def test_quest_completion_is_idempotent(migrated_database_path: Path) -> None:
    """Completing the same quest twice stores one completion."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        attempt_id = record_quest_attempt(database_connection, _attempt())
        completion = QuestCompletion(
            handle="alice",
            course_id=COURSE_ID,
            quest_id="prove-shell-alive",
            attempt_id=attempt_id,
            completed_at=TIMESTAMP,
            source="chat",
        )

        complete_quest(database_connection, completion)
        complete_quest(database_connection, completion)

        assert (
            get_quest_completion(
                database_connection,
                "alice",
                COURSE_ID,
                "prove-shell-alive",
            )
            == completion
        )


def test_quest_completion_rejects_failed_attempt(migrated_database_path: Path) -> None:
    """A failed validation attempt cannot complete a quest."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        attempt_id = record_quest_attempt(database_connection, _attempt(outcome="failed"))

        with pytest.raises(RepositoryError, match="quest completion attempt did not pass"):
            complete_quest(
                database_connection,
                QuestCompletion(
                    handle="alice",
                    course_id=COURSE_ID,
                    quest_id="prove-shell-alive",
                    attempt_id=attempt_id,
                    completed_at=TIMESTAMP,
                    source="chat",
                ),
            )


def test_quest_completion_rejects_mismatched_attempt(migrated_database_path: Path) -> None:
    """A passed attempt for another quest cannot complete this quest."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        attempt_id = record_quest_attempt(database_connection, _attempt(quest_id="name-system"))

        with pytest.raises(RepositoryError, match="quest completion attempt does not match"):
            complete_quest(
                database_connection,
                QuestCompletion(
                    handle="alice",
                    course_id=COURSE_ID,
                    quest_id="prove-shell-alive",
                    attempt_id=attempt_id,
                    completed_at=TIMESTAMP,
                    source="chat",
                ),
            )


def test_quest_completion_schema_rejects_mismatched_attempt(
    migrated_database_path: Path,
) -> None:
    """The SQLite trigger guards writes that bypass repository code."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        attempt_id = record_quest_attempt(database_connection, _attempt(quest_id="name-system"))

        with pytest.raises(sqlite3.IntegrityError, match="quest completion attempt"):
            database_connection.execute(
                """
                insert into quest_completions
                    (handle, course_id, quest_id, attempt_id, completed_at, source)
                values (?, ?, ?, ?, ?, ?)
                """,
                ("alice", COURSE_ID, "prove-shell-alive", attempt_id, TIMESTAMP, "chat"),
            )


def test_quest_attempt_schema_rejects_attempt_mutation(migrated_database_path: Path) -> None:
    """Quest attempts are append-only after being recorded."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        attempt_id = record_quest_attempt(database_connection, _attempt())

        with pytest.raises(sqlite3.IntegrityError, match="quest attempts are append-only"):
            database_connection.execute(
                "update quest_attempts set outcome = ? where id = ?",
                ("failed", attempt_id),
            )


def _attempt(quest_id: str = "prove-shell-alive", outcome: str = "passed") -> QuestAttempt:
    return QuestAttempt(
        id=None,
        handle="alice",
        course_id=COURSE_ID,
        quest_id=quest_id,
        attempted_at=TIMESTAMP,
        source="chat",
        outcome=outcome,
        failure_reason=None if outcome == "passed" else "missing command",
        evidence={"command": "man ls", "passed": outcome == "passed"},
    )
