"""Tests for command observation repository functions."""

from __future__ import annotations

from pathlib import Path

from maker_guide.repositories.command_observation import (
    CommandObservation,
    add_command_observation,
    delete_command_observations_before,
    list_recent_command_observations,
)
from maker_guide.repositories.helpers import connect_database
from tests.repositories.helpers import COURSE_ID, TIMESTAMP, write_learner


def test_command_observation_lists_recent_successful_course_commands(
    migrated_database_path: Path,
) -> None:
    """Recent command observations are scoped to successful course work."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        add_command_observation(
            database_connection,
            _command_observation(command="pwd", observed_at=TIMESTAMP),
        )
        add_command_observation(
            database_connection,
            _command_observation(command="ls", observed_at="2026-07-11T09:02:00Z"),
        )
        add_command_observation(
            database_connection,
            _command_observation(
                command="wrong course",
                course_id="other-course",
                observed_at="2026-07-11T09:03:00Z",
            ),
        )
        add_command_observation(
            database_connection,
            _command_observation(
                command="failed",
                exit_status=1,
                observed_at="2026-07-11T09:04:00Z",
            ),
        )
        add_command_observation(
            database_connection,
            _command_observation(
                command="before",
                phase="before",
                exit_status=None,
                observed_at="2026-07-11T09:05:00Z",
            ),
        )

        assert [
            observation.command
            for observation in list_recent_command_observations(
                database_connection,
                "alice",
                COURSE_ID,
                observed_since="2026-07-11T09:01:00Z",
                limit=5,
            )
        ] == ["ls"]


def test_command_observation_deletes_raw_rows_before_cutoff(
    migrated_database_path: Path,
) -> None:
    """Retention deletes only matching course observations before the cutoff."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        add_command_observation(
            database_connection,
            _command_observation(command="old", observed_at="2026-11-28T23:59:59Z"),
        )
        add_command_observation(
            database_connection,
            _command_observation(command="kept", observed_at="2026-11-29T00:00:00Z"),
        )
        add_command_observation(
            database_connection,
            _command_observation(
                command="other-course",
                course_id="other-course",
                observed_at="2026-11-28T23:59:59Z",
            ),
        )

        assert (
            delete_command_observations_before(
                database_connection,
                COURSE_ID,
                "2026-11-29T00:00:00Z",
            )
            == 1
        )

        assert [
            observation.command
            for observation in list_recent_command_observations(
                database_connection,
                "alice",
                COURSE_ID,
                observed_since="0000-01-01T00:00:00Z",
                limit=10,
            )
        ] == ["kept"]


def test_command_observation_ignores_a_replayed_event(
    migrated_database_path: Path,
) -> None:
    """A retried hook event cannot duplicate command evidence."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        observation = _command_observation(command="pwd", observed_at=TIMESTAMP)
        assert add_command_observation(database_connection, observation) is not None
        assert (
            add_command_observation(
                database_connection,
                CommandObservation(
                    id=None,
                    event_id="event-1",
                    handle=observation.handle,
                    course_id=observation.course_id,
                    command=observation.command,
                    cwd=observation.cwd,
                    phase=observation.phase,
                    exit_status=observation.exit_status,
                    observed_at=observation.observed_at,
                ),
            )
            is not None
        )
        assert (
            add_command_observation(
                database_connection,
                CommandObservation(
                    id=None,
                    event_id="event-1",
                    handle=observation.handle,
                    course_id=observation.course_id,
                    command=observation.command,
                    cwd=observation.cwd,
                    phase=observation.phase,
                    exit_status=observation.exit_status,
                    observed_at=observation.observed_at,
                ),
            )
            is None
        )


def _command_observation(
    command: str,
    observed_at: str,
    course_id: str = COURSE_ID,
    phase: str = "after",
    exit_status: int | None = 0,
) -> CommandObservation:
    return CommandObservation(
        id=None,
        handle="alice",
        course_id=course_id,
        command=command,
        cwd="/home/alice",
        phase=phase,
        exit_status=exit_status,
        observed_at=observed_at,
    )
