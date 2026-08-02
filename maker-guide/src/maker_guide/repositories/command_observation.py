"""Command observation repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast

from maker_guide.repositories.helpers import last_inserted_id


@dataclass(frozen=True, kw_only=True, slots=True)
class CommandObservation:
    """Selected shell command observation."""

    id: int | None
    """SQLite-generated observation id, absent before insert."""
    handle: str
    """Shared learner id."""
    course_id: str
    """Course id from the Python curriculum catalog."""
    command: str
    """Observed shell command text."""
    cwd: str
    """Current working directory at observation time."""
    phase: str
    """Observation phase, before or after command execution."""
    exit_status: int | None
    """Command exit status for after observations."""
    observed_at: str
    """ISO timestamp for when the command was observed."""
    event_id: str | None = None
    """Stable hook event identity, absent for legacy observations."""


def add_command_observation(
    database_connection: sqlite3.Connection,
    observation: CommandObservation,
) -> int | None:
    """Insert a command observation, returning None when the event was seen already."""
    cursor = database_connection.execute(
        """
            insert into command_observations
                (event_id, handle, course_id, command, cwd, phase, exit_status, observed_at)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            on conflict do nothing
            """,
        (
            observation.event_id,
            observation.handle,
            observation.course_id,
            observation.command,
            observation.cwd,
            observation.phase,
            observation.exit_status,
            observation.observed_at,
        ),
    )
    return last_inserted_id(cursor) if cursor.rowcount else None


def delete_command_observations_before(
    database_connection: sqlite3.Connection,
    course_id: str,
    observed_before: str,
) -> int:
    """Delete raw command observations before an ISO timestamp."""
    cursor = database_connection.execute(
        """
        delete from command_observations
        where course_id = ? and observed_at < ?
        """,
        (course_id, observed_before),
    )
    return cursor.rowcount


def list_recent_command_observations(  # noqa: PLR0913 - Query scope and time bounds are explicit.
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
    observed_since: str,
    limit: int,
    *,
    observed_through: str | None = None,
) -> list[CommandObservation]:
    """Return bounded successful after-command observations for a learner course."""
    observation_records = cast(
        "list[tuple[int, str | None, str, str, str, str, str, int | None, str]]",
        database_connection.execute(
            """
            select id, event_id, handle, course_id, command, cwd, phase, exit_status, observed_at
            from command_observations
            where handle = ?
                and course_id = ?
                and phase = 'after'
                and exit_status = 0
                and observed_at >= ?
                and (? is null or observed_at <= ?)
            order by observed_at desc, id desc
            limit ?
            """,
            (handle, course_id, observed_since, observed_through, observed_through, limit),
        ).fetchall(),
    )
    return [
        CommandObservation(
            id=observation_record[0],
            event_id=observation_record[1],
            handle=observation_record[2],
            course_id=observation_record[3],
            command=observation_record[4],
            cwd=observation_record[5],
            phase=observation_record[6],
            exit_status=observation_record[7],
            observed_at=observation_record[8],
        )
        for observation_record in observation_records
    ]
