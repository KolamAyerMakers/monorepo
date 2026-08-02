"""Durable session objective completion repository."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast


@dataclass(frozen=True, kw_only=True, slots=True)
class SessionObjectiveCompletion:
    """One durable validator-backed objective completion."""

    handle: str
    course_id: str
    session_id: str
    objective_id: str
    completed_at: str
    evidence_json: str


def list_completed_objective_ids(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
    session_id: str,
) -> frozenset[str]:
    """Return completed objective ids for one learner and session."""
    return frozenset(
        record[0]
        for record in cast(
            "list[tuple[str]]",
            database_connection.execute(
                """select objective_id from session_objective_completions
                where handle = ? and course_id = ? and session_id = ?""",
                (handle, course_id, session_id),
            ).fetchall(),
        )
    )


def complete_session_objective(
    database_connection: sqlite3.Connection,
    completion: SessionObjectiveCompletion,
) -> None:
    """Record objective completion once."""
    database_connection.execute(
        """insert or ignore into session_objective_completions
        (handle, course_id, session_id, objective_id, completed_at, evidence_json)
        values (?, ?, ?, ?, ?, ?)""",
        (
            completion.handle,
            completion.course_id,
            completion.session_id,
            completion.objective_id,
            completion.completed_at,
            completion.evidence_json,
        ),
    )


def count_session_objective_completions(
    database_connection: sqlite3.Connection,
    course_id: str,
    session_id: str,
    objective_id: str,
) -> int:
    """Return the number of learners who completed a session objective."""
    completion_count_record = cast(
        "tuple[int]",
        database_connection.execute(
            """
            select count(*)
            from session_objective_completions
            where course_id = ? and session_id = ? and objective_id = ?
            """,
            (course_id, session_id, objective_id),
        ).fetchone(),
    )
    return completion_count_record[0]


def count_rank_eligible_session_objective_completions(
    database_connection: sqlite3.Connection,
    course_id: str,
    session_id: str,
    objective_id: str,
) -> int:
    """Return rank-eligible learners who completed a session objective."""
    completion_count_record = cast(
        "tuple[int]",
        database_connection.execute(
            """
            select count(*)
            from session_objective_completions
            join cohort_memberships
                on cohort_memberships.handle = session_objective_completions.handle
                and cohort_memberships.course_id = session_objective_completions.course_id
            where session_objective_completions.course_id = ?
                and session_objective_completions.session_id = ?
                and session_objective_completions.objective_id = ?
                and cohort_memberships.rank_eligible = 1
            """,
            (course_id, session_id, objective_id),
        ).fetchone(),
    )
    return completion_count_record[0]
