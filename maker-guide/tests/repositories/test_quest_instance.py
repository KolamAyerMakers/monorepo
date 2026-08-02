"""Tests for quest instance repository functions."""

from __future__ import annotations

from pathlib import Path

from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.quest_instance import (
    QuestInstance,
    get_quest_instance,
    upsert_quest_instance,
)
from tests.repositories.helpers import COURSE_ID, TIMESTAMP, write_learner


def test_quest_instance_round_trips_generated_data(migrated_database_path: Path) -> None:
    """Generated quest metadata round-trips through JSON storage."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        upsert_quest_instance(database_connection, _instance(seed="seed-1"))
        upsert_quest_instance(database_connection, _instance(seed="seed-2"))

        assert get_quest_instance(
            database_connection,
            "alice",
            COURSE_ID,
            "prove-shell-alive",
        ) == _instance(seed="seed-2")


def _instance(seed: str) -> QuestInstance:
    return QuestInstance(
        handle="alice",
        course_id=COURSE_ID,
        quest_id="prove-shell-alive",
        seed=seed,
        generated_at=TIMESTAMP,
        expected_answer_hash="hash-1",
        data={"path": "/makers/alice/prove-shell-alive.txt"},
    )
