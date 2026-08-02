"""Course release repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast


@dataclass(frozen=True, kw_only=True, slots=True)
class CourseRelease:
    """Globally released course session."""

    course_id: str
    session_reached: str
    released_at: str


def get_course_release(
    database_connection: sqlite3.Connection,
    course_id: str,
) -> CourseRelease | None:
    """Return a course's global release state."""
    release_record = cast(
        "tuple[str, str, str] | None",
        database_connection.execute(
            """
            select course_id, session_reached, released_at
            from course_releases
            where course_id = ?
            """,
            (course_id,),
        ).fetchone(),
    )
    if release_record is None:
        return None
    return CourseRelease(
        course_id=release_record[0],
        session_reached=release_record[1],
        released_at=release_record[2],
    )


def get_course_session_released_at(
    database_connection: sqlite3.Connection,
    course_id: str,
    session_id: str,
) -> str | None:
    """Return the canonical audit timestamp for a course session release."""
    release_record = cast(
        "tuple[str] | None",
        database_connection.execute(
            """
            select created_at
            from audit_events
            where event_type = 'course_released'
                and handle is null
                and json_extract(payload_json, '$.course_id') = ?
                and json_extract(payload_json, '$.session_reached') = ?
            order by id
            limit 1
            """,
            (course_id, session_id),
        ).fetchone(),
    )
    return None if release_record is None else release_record[0]


def upsert_course_release(
    database_connection: sqlite3.Connection,
    course_release: CourseRelease,
) -> None:
    """Insert or update a course's global release state."""
    database_connection.execute(
        """
        insert into course_releases (course_id, session_reached, released_at)
        values (?, ?, ?)
        on conflict(course_id) do update set
            session_reached = excluded.session_reached,
            released_at = excluded.released_at
        """,
        (course_release.course_id, course_release.session_reached, course_release.released_at),
    )
