"""Quest assignment repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast

from maker_guide.repositories.helpers import RepositoryError


@dataclass(frozen=True, kw_only=True, slots=True)
class QuestAssignment:
    """Learner-specific quest assignment."""

    id: int | None
    """SQLite-generated assignment id, absent before insert."""
    handle: str
    """Shared learner id."""
    course_id: str
    """Course id from the Python curriculum catalog."""
    quest_id: str
    """Quest id from the Python curriculum catalog."""
    assigned_at: str
    """ISO timestamp for when the quest was assigned."""
    source: str
    """Source that assigned the quest."""


def assign_quest(database_connection: sqlite3.Connection, assignment: QuestAssignment) -> int:
    """Idempotently assign a quest and return the assignment id."""
    database_connection.execute(
        """
        insert or ignore into quest_assignments
            (handle, course_id, quest_id, assigned_at, source)
        values (?, ?, ?, ?, ?)
        """,
        (
            assignment.handle,
            assignment.course_id,
            assignment.quest_id,
            assignment.assigned_at,
            assignment.source,
        ),
    )
    return _assignment_id(
        database_connection,
        assignment.handle,
        assignment.course_id,
        assignment.quest_id,
    )


def get_assignment(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
    quest_id: str,
) -> QuestAssignment | None:
    """Return a quest assignment."""
    assignment_record = cast(
        "tuple[int, str, str, str, str, str] | None",
        database_connection.execute(
            """
            select id, handle, course_id, quest_id, assigned_at, source
            from quest_assignments
            where handle = ? and course_id = ? and quest_id = ?
            """,
            (handle, course_id, quest_id),
        ).fetchone(),
    )
    if assignment_record is None:
        return None
    return QuestAssignment(
        id=assignment_record[0],
        handle=assignment_record[1],
        course_id=assignment_record[2],
        quest_id=assignment_record[3],
        assigned_at=assignment_record[4],
        source=assignment_record[5],
    )


def list_assignments(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
) -> list[QuestAssignment]:
    """Return all quest assignments for a learner course."""
    assignment_records = cast(
        "list[tuple[int, str, str, str, str, str]]",
        database_connection.execute(
            """
            select id, handle, course_id, quest_id, assigned_at, source
            from quest_assignments
            where handle = ? and course_id = ?
            order by id
            """,
            (handle, course_id),
        ).fetchall(),
    )
    return [_assignment_from_record(assignment_record) for assignment_record in assignment_records]


def _assignment_from_record(
    assignment_record: tuple[int, str, str, str, str, str],
) -> QuestAssignment:
    return QuestAssignment(
        id=assignment_record[0],
        handle=assignment_record[1],
        course_id=assignment_record[2],
        quest_id=assignment_record[3],
        assigned_at=assignment_record[4],
        source=assignment_record[5],
    )


def _assignment_id(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
    quest_id: str,
) -> int:
    assignment_id_record = cast(
        "tuple[int] | None",
        database_connection.execute(
            """
            select id from quest_assignments
            where handle = ? and course_id = ? and quest_id = ?
            """,
            (handle, course_id, quest_id),
        ).fetchone(),
    )
    if assignment_id_record is None:
        raise RepositoryError("quest assignment was not written")
    return assignment_id_record[0]
