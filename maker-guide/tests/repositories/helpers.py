"""Shared helpers for repository tests."""

from __future__ import annotations

import sqlite3

from maker_guide.repositories.learner import Learner, upsert_learner

COURSE_ID = "lf2607"
TIMESTAMP = "2026-07-11T09:00:00Z"


def learner(handle: str = "alice", tagline: str = "ready") -> Learner:
    """Return a standard test learner."""
    return Learner(
        handle=handle,
        joined_at=TIMESTAMP,
        tagline=tagline,
        created_at=TIMESTAMP,
    )


def write_learner(database_connection: sqlite3.Connection, handle: str = "alice") -> None:
    """Insert the standard test learner."""
    upsert_learner(database_connection, learner(handle=handle))
