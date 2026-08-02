"""Cohort membership repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast


@dataclass(frozen=True, kw_only=True, slots=True)
class CohortMembership:
    """Learner membership in a course cohort."""

    handle: str
    """Shared learner id."""
    course_id: str
    """Course id from the Python curriculum catalog."""
    joined_at: str
    """ISO timestamp for when the learner joined this cohort."""
    rank_eligible: bool = True
    """Whether the learner is eligible for cohort rankings."""


def upsert_membership(
    database_connection: sqlite3.Connection,
    membership: CohortMembership,
) -> None:
    """Insert or update a cohort membership."""
    database_connection.execute(
        """
        insert into cohort_memberships (handle, course_id, joined_at, rank_eligible)
        values (?, ?, ?, ?)
        on conflict(handle, course_id) do update set
            joined_at = excluded.joined_at,
            rank_eligible = excluded.rank_eligible
        """,
        (
            membership.handle,
            membership.course_id,
            membership.joined_at,
            membership.rank_eligible,
        ),
    )


def get_membership(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
) -> CohortMembership | None:
    """Return a cohort membership."""
    membership_record = cast(
        "tuple[str, str, str, int] | None",
        database_connection.execute(
            """
            select handle, course_id, joined_at, rank_eligible
            from cohort_memberships
            where handle = ? and course_id = ?
            """,
            (handle, course_id),
        ).fetchone(),
    )
    if membership_record is None:
        return None
    return CohortMembership(
        handle=membership_record[0],
        course_id=membership_record[1],
        joined_at=membership_record[2],
        rank_eligible=bool(membership_record[3]),
    )


def list_memberships(
    database_connection: sqlite3.Connection,
    course_id: str,
) -> tuple[CohortMembership, ...]:
    """Return cohort memberships for a course."""
    return tuple(
        CohortMembership(
            handle=membership_record[0],
            course_id=membership_record[1],
            joined_at=membership_record[2],
            rank_eligible=bool(membership_record[3]),
        )
        for membership_record in cast(
            "list[tuple[str, str, str, int]]",
            database_connection.execute(
                """
                select handle, course_id, joined_at, rank_eligible
                from cohort_memberships
                where course_id = ?
                order by handle
                """,
                (course_id,),
            ).fetchall(),
        )
    )
