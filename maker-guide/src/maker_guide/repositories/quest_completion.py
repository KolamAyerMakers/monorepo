"""Quest completion repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast

from maker_guide.repositories.helpers import RepositoryError


@dataclass(frozen=True, kw_only=True, slots=True)
class QuestCompletion:
    """Completed learner quest."""

    handle: str
    """Shared learner id."""
    course_id: str
    """Course id from the Python curriculum catalog."""
    quest_id: str
    """Quest id from the Python curriculum catalog."""
    attempt_id: int | None
    """Optional id of the validation attempt that completed the quest."""
    completed_at: str
    """ISO timestamp for when the quest was completed."""
    source: str
    """Source that recorded completion."""


def complete_quest(database_connection: sqlite3.Connection, completion: QuestCompletion) -> None:
    """Idempotently record quest completion."""
    _ensure_completion_attempt_matches(database_connection, completion)
    database_connection.execute(
        """
        insert or ignore into quest_completions
            (handle, course_id, quest_id, attempt_id, completed_at, source)
        values (?, ?, ?, ?, ?, ?)
        """,
        (
            completion.handle,
            completion.course_id,
            completion.quest_id,
            completion.attempt_id,
            completion.completed_at,
            completion.source,
        ),
    )


def _ensure_completion_attempt_matches(
    database_connection: sqlite3.Connection,
    completion: QuestCompletion,
) -> None:
    if completion.attempt_id is None:
        return
    attempt_record = cast(
        "tuple[str] | None",
        database_connection.execute(
            """
            select outcome
            from quest_attempts
            where id = ? and handle = ? and course_id = ? and quest_id = ?
            """,
            (
                completion.attempt_id,
                completion.handle,
                completion.course_id,
                completion.quest_id,
            ),
        ).fetchone(),
    )
    if attempt_record is None:
        raise RepositoryError("quest completion attempt does not match completion")
    if attempt_record[0] != "passed":
        raise RepositoryError("quest completion attempt did not pass")


def get_quest_completion(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
    quest_id: str,
) -> QuestCompletion | None:
    """Return a quest completion."""
    completion_record = cast(
        "tuple[str, str, str, int | None, str, str] | None",
        database_connection.execute(
            """
            select handle, course_id, quest_id, attempt_id, completed_at, source
            from quest_completions
            where handle = ? and course_id = ? and quest_id = ?
            """,
            (handle, course_id, quest_id),
        ).fetchone(),
    )
    if completion_record is None:
        return None
    return QuestCompletion(
        handle=completion_record[0],
        course_id=completion_record[1],
        quest_id=completion_record[2],
        attempt_id=completion_record[3],
        completed_at=completion_record[4],
        source=completion_record[5],
    )


def list_quest_completions(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
) -> list[QuestCompletion]:
    """Return all quest completions for a learner course."""
    completion_records = cast(
        "list[tuple[str, str, str, int | None, str, str]]",
        database_connection.execute(
            """
            select handle, course_id, quest_id, attempt_id, completed_at, source
            from quest_completions
            where handle = ? and course_id = ?
            order by completed_at, quest_id
            """,
            (handle, course_id),
        ).fetchall(),
    )
    return [_completion_from_record(completion_record) for completion_record in completion_records]


def count_quest_completions(
    database_connection: sqlite3.Connection,
    course_id: str,
    quest_id: str,
) -> int:
    """Return the number of learners who completed a course quest."""
    completion_count_record = cast(
        "tuple[int]",
        database_connection.execute(
            """
            select count(*)
            from quest_completions
            where course_id = ? and quest_id = ?
            """,
            (course_id, quest_id),
        ).fetchone(),
    )
    return completion_count_record[0]


def count_rank_eligible_quest_completions(
    database_connection: sqlite3.Connection,
    course_id: str,
    quest_id: str,
) -> int:
    """Return rank-eligible learners who completed a course quest."""
    completion_count_record = cast(
        "tuple[int]",
        database_connection.execute(
            """
            select count(*)
            from quest_completions
            join cohort_memberships
                on cohort_memberships.handle = quest_completions.handle
                and cohort_memberships.course_id = quest_completions.course_id
            where quest_completions.course_id = ?
                and quest_completions.quest_id = ?
                and cohort_memberships.rank_eligible = 1
            """,
            (course_id, quest_id),
        ).fetchone(),
    )
    return completion_count_record[0]


def list_completed_quest_ids(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
) -> frozenset[str]:
    """Return completed quest ids for a learner course."""
    completion_records = cast(
        "list[tuple[str]]",
        database_connection.execute(
            """
            select quest_id
            from quest_completions
            where handle = ? and course_id = ?
            """,
            (handle, course_id),
        ).fetchall(),
    )
    return frozenset(quest_id for (quest_id,) in completion_records)


def _completion_from_record(
    completion_record: tuple[str, str, str, int | None, str, str],
) -> QuestCompletion:
    return QuestCompletion(
        handle=completion_record[0],
        course_id=completion_record[1],
        quest_id=completion_record[2],
        attempt_id=completion_record[3],
        completed_at=completion_record[4],
        source=completion_record[5],
    )
