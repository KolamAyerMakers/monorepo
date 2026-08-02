"""Quest instance repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast

from maker_guide.repositories.helpers import JsonPayload, dump_json, load_json


@dataclass(frozen=True, kw_only=True, slots=True)
class QuestInstance:
    """Generated per-learner quest data."""

    handle: str
    """Shared learner id."""
    course_id: str
    """Course id from the Python curriculum catalog."""
    quest_id: str
    """Quest id from the Python curriculum catalog."""
    seed: str
    """Seed used to generate learner-specific quest data."""
    generated_at: str
    """ISO timestamp for when quest data was generated."""
    expected_answer_hash: str | None
    """Optional hash of the expected generated answer."""
    data: JsonPayload
    """Non-secret generated quest metadata."""


def upsert_quest_instance(database_connection: sqlite3.Connection, instance: QuestInstance) -> None:
    """Insert or update generated quest data."""
    database_connection.execute(
        """
        insert into quest_instances
            (handle, course_id, quest_id, seed, generated_at, expected_answer_hash, data_json)
        values (?, ?, ?, ?, ?, ?, ?)
        on conflict(handle, course_id, quest_id) do update set
            seed = excluded.seed,
            generated_at = excluded.generated_at,
            expected_answer_hash = excluded.expected_answer_hash,
            data_json = excluded.data_json
        """,
        (
            instance.handle,
            instance.course_id,
            instance.quest_id,
            instance.seed,
            instance.generated_at,
            instance.expected_answer_hash,
            dump_json(instance.data),
        ),
    )


def get_quest_instance(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
    quest_id: str,
) -> QuestInstance | None:
    """Return generated quest data."""
    instance_record = cast(
        "tuple[str, str, str, str, str, str | None, str] | None",
        database_connection.execute(
            """
            select handle, course_id, quest_id, seed, generated_at,
                expected_answer_hash, data_json
            from quest_instances
            where handle = ? and course_id = ? and quest_id = ?
            """,
            (handle, course_id, quest_id),
        ).fetchone(),
    )
    if instance_record is None:
        return None
    return QuestInstance(
        handle=instance_record[0],
        course_id=instance_record[1],
        quest_id=instance_record[2],
        seed=instance_record[3],
        generated_at=instance_record[4],
        expected_answer_hash=instance_record[5],
        data=load_json(instance_record[6]),
    )
