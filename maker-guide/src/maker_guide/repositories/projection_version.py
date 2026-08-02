"""Projection version repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast


@dataclass(frozen=True, kw_only=True, slots=True)
class ProjectionVersion:
    """Last written projection version."""

    name: str
    """Projection name."""
    last_written_at: str
    """ISO timestamp for when the projection was last written."""
    version: int
    """Projection format or write version."""


def upsert_projection_version(
    database_connection: sqlite3.Connection,
    projection: ProjectionVersion,
) -> None:
    """Insert or update a projection version."""
    database_connection.execute(
        """
        insert into projection_versions (name, last_written_at, version)
        values (?, ?, ?)
        on conflict(name) do update set
            last_written_at = excluded.last_written_at,
            version = excluded.version
        """,
        (projection.name, projection.last_written_at, projection.version),
    )


def get_projection_version(
    database_connection: sqlite3.Connection,
    name: str,
) -> ProjectionVersion | None:
    """Return a projection version."""
    projection_record = cast(
        "tuple[str, str, int] | None",
        database_connection.execute(
            "select name, last_written_at, version from projection_versions where name = ?",
            (name,),
        ).fetchone(),
    )
    if projection_record is None:
        return None
    return ProjectionVersion(
        name=projection_record[0],
        last_written_at=projection_record[1],
        version=projection_record[2],
    )
