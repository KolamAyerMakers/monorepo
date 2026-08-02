"""Tests for projection version repository functions."""

from __future__ import annotations

from pathlib import Path

from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.projection_version import (
    ProjectionVersion,
    get_projection_version,
    upsert_projection_version,
)
from tests.repositories.helpers import TIMESTAMP


def test_projection_version_upsert_reads_and_updates(migrated_database_path: Path) -> None:
    """Projection version state can be inserted, read, and updated idempotently."""
    with connect_database(migrated_database_path) as database_connection:
        upsert_projection_version(database_connection, _projection(version=1))
        upsert_projection_version(database_connection, _projection(version=2))

        assert get_projection_version(database_connection, "makers") == _projection(version=2)


def _projection(version: int) -> ProjectionVersion:
    return ProjectionVersion(name="makers", last_written_at=TIMESTAMP, version=version)
