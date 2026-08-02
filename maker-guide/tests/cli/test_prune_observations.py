"""Tests for raw observation pruning CLI."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from maker_guide.cli.prune_observations import run
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.repositories.command_observation import (
    CommandObservation,
    add_command_observation,
    list_recent_command_observations,
)
from maker_guide.repositories.helpers import connect_database
from tests.repositories.helpers import write_learner


def test_prune_observations_cli_deletes_expired_raw_observations(
    migrated_database_path: Path,
) -> None:
    """The CLI prunes observations from the configured database path."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        add_command_observation(database_connection, _command_observation())

    assert (
        run(
            [
                "--database",
                str(migrated_database_path),
                "--today",
                (CATALOG.course.ends_on + timedelta(days=31)).isoformat(),
            ],
        )
        == 0
    )

    with connect_database(migrated_database_path) as database_connection:
        assert (
            list_recent_command_observations(
                database_connection,
                "alice",
                CATALOG.course.id,
                observed_since="0000-01-01T00:00:00Z",
                limit=10,
            )
            == []
        )


def _command_observation() -> CommandObservation:
    return CommandObservation(
        id=None,
        handle="alice",
        course_id=CATALOG.course.id,
        command="whoami",
        cwd="/home/alice",
        phase="after",
        exit_status=0,
        observed_at="2026-07-19T09:00:00Z",
    )
