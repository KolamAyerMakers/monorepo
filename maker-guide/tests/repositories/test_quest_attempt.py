"""Tests for quest attempt repository functions."""

from __future__ import annotations

from pathlib import Path

from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.quest_attempt import (
    QuestAttempt,
    get_quest_attempt,
    record_quest_attempt,
)
from tests.repositories.helpers import COURSE_ID, TIMESTAMP, write_learner


def test_quest_attempt_round_trips_json_evidence(migrated_database_path: Path) -> None:
    """Quest attempts preserve validation evidence JSON."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        attempt_id = record_quest_attempt(database_connection, _attempt())

        assert get_quest_attempt(database_connection, attempt_id) == _attempt(
            quest_attempt_id=attempt_id,
        )


def _attempt(quest_attempt_id: int | None = None) -> QuestAttempt:
    return QuestAttempt(
        id=quest_attempt_id,
        handle="alice",
        course_id=COURSE_ID,
        quest_id="prove-shell-alive",
        attempted_at=TIMESTAMP,
        source="chat",
        outcome="failed",
        failure_reason="missing command",
        evidence={"command": "man ls", "passed": False},
    )
