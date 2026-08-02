"""Tests for global course release repository functions."""

from __future__ import annotations

from pathlib import Path

from maker_guide.repositories.course_release import (
    CourseRelease,
    get_course_release,
    upsert_course_release,
)
from maker_guide.repositories.helpers import connect_database

COURSE_ID = "lf2607"


def test_course_release_upsert_reads_and_updates(migrated_database_path: Path) -> None:
    """A course has one shared release state."""
    with connect_database(migrated_database_path) as database_connection:
        first_release = CourseRelease(
            course_id=COURSE_ID,
            session_reached="S1",
            released_at="2026-07-18T09:00:00Z",
        )
        upsert_course_release(database_connection, first_release)
        assert get_course_release(database_connection, COURSE_ID) == first_release

        second_release = CourseRelease(
            course_id=COURSE_ID,
            session_reached="S2",
            released_at="2026-07-25T09:00:00Z",
        )
        upsert_course_release(database_connection, second_release)

        assert get_course_release(database_connection, COURSE_ID) == second_release
