"""Tests for quest assignment repository functions."""

from __future__ import annotations

from pathlib import Path

from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.quest_assignment import QuestAssignment, assign_quest, get_assignment
from tests.repositories.helpers import COURSE_ID, TIMESTAMP, write_learner


def test_quest_assignment_is_idempotent(migrated_database_path: Path) -> None:
    """Assigning the same quest twice returns the same stored assignment."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        assignment = QuestAssignment(
            id=None,
            handle="alice",
            course_id=COURSE_ID,
            quest_id="prove-shell-alive",
            assigned_at=TIMESTAMP,
            source="chat",
        )

        assignment_id = assign_quest(database_connection, assignment)
        duplicate_assignment_id = assign_quest(database_connection, assignment)

        assert duplicate_assignment_id == assignment_id
        assert get_assignment(
            database_connection,
            "alice",
            COURSE_ID,
            "prove-shell-alive",
        ) == QuestAssignment(
            id=assignment_id,
            handle="alice",
            course_id=COURSE_ID,
            quest_id="prove-shell-alive",
            assigned_at=TIMESTAMP,
            source="chat",
        )
