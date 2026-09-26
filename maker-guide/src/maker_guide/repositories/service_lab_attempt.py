"""One durable, idempotent fault attempt per learner session objective."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast

from maker_guide.service_lab import ServiceLabScenario


@dataclass(frozen=True, kw_only=True, slots=True)
class ServiceLabAttempt:
    """Durable launch identity; health is always inspected again, never cached."""

    handle: str
    course_id: str
    session_id: str
    objective_id: str
    run_id: str
    scenario: ServiceLabScenario
    message_index: int
    created_at: str
    started_at: str | None = None


def get_attempt(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
    session_id: str,
    objective_id: str,
) -> ServiceLabAttempt | None:
    """Load identity and launch state, never cached health observations."""
    record = cast(
        "tuple[str, str, int, str, str | None] | None",
        database_connection.execute(
            """select run_id, scenario, message_index, created_at, started_at
            from service_lab_attempts
            where handle = ? and course_id = ? and session_id = ? and objective_id = ?""",
            (handle, course_id, session_id, objective_id),
        ).fetchone(),
    )
    if record is None:
        return None
    return ServiceLabAttempt(
        handle=handle,
        course_id=course_id,
        session_id=session_id,
        objective_id=objective_id,
        run_id=record[0],
        scenario=cast("ServiceLabScenario", record[1]),
        message_index=record[2],
        created_at=record[3],
        started_at=record[4],
    )


def reserve_attempt(database_connection: sqlite3.Connection, attempt: ServiceLabAttempt) -> None:
    """Keep the winner's run identity when two requests select the same objective."""
    database_connection.execute(
        """insert or ignore into service_lab_attempts
        (handle, course_id, session_id, objective_id, run_id, scenario, message_index, created_at)
        values (?, ?, ?, ?, ?, ?,
            (select count(*) from service_lab_attempts where handle = ? and course_id = ?), ?)
        """,
        (
            attempt.handle,
            attempt.course_id,
            attempt.session_id,
            attempt.objective_id,
            attempt.run_id,
            attempt.scenario,
            attempt.handle,
            attempt.course_id,
            attempt.created_at,
        ),
    )


def mark_started(database_connection: sqlite3.Connection, run_id: str, timestamp: str) -> bool:
    """Acknowledge a witnessed injection once; later reports cannot reset it."""
    return (
        database_connection.execute(
            """update service_lab_attempts set started_at = ?
            where run_id = ? and started_at is null""",
            (timestamp, run_id),
        ).rowcount
        == 1
    )
