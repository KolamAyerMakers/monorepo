"""Tests for cohort membership repository functions."""

from __future__ import annotations

from pathlib import Path

from maker_guide.repositories.cohort_membership import (
    CohortMembership,
    get_membership,
    list_memberships,
    upsert_membership,
)
from maker_guide.repositories.helpers import connect_database
from tests.repositories.helpers import COURSE_ID, TIMESTAMP, write_learner


def test_membership_upsert_reads_and_updates(migrated_database_path: Path) -> None:
    """Cohort membership rows can be inserted, read, and updated idempotently."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        upsert_membership(database_connection, _membership())
        assert get_membership(database_connection, "alice", COURSE_ID) == _membership()

        upsert_membership(
            database_connection,
            _membership(joined_at="2026-07-19T09:00:00Z", rank_eligible=False),
        )
        assert get_membership(database_connection, "alice", COURSE_ID) == _membership(
            joined_at="2026-07-19T09:00:00Z",
            rank_eligible=False,
        )


def test_memberships_list_by_course(migrated_database_path: Path) -> None:
    """Cohort membership rows can be listed for a course."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        write_learner(database_connection, handle="bob")
        upsert_membership(database_connection, _membership())
        upsert_membership(database_connection, _membership(handle="bob"))

        assert list_memberships(database_connection, COURSE_ID) == (
            _membership(),
            _membership(handle="bob"),
        )


def _membership(
    handle: str = "alice",
    joined_at: str = TIMESTAMP,
    *,
    rank_eligible: bool = True,
) -> CohortMembership:
    return CohortMembership(
        handle=handle,
        course_id=COURSE_ID,
        joined_at=joined_at,
        rank_eligible=rank_eligible,
    )
