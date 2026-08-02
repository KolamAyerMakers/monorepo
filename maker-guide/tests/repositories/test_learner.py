"""Tests for learner repository functions."""

from __future__ import annotations

from pathlib import Path

import pytest

from maker_guide.repositories.helpers import RepositoryError, connect_database
from maker_guide.repositories.learner import get_learner, upsert_learner
from tests.repositories.helpers import learner


def test_learner_upsert_reads_and_updates(migrated_database_path: Path) -> None:
    """Learner rows can be inserted, read, and updated idempotently."""
    with connect_database(migrated_database_path) as database_connection:
        upsert_learner(database_connection, learner(tagline="first"))
        assert get_learner(database_connection, "alice") == learner(tagline="first")

        upsert_learner(database_connection, learner(tagline="updated"))
        assert get_learner(database_connection, "alice") == learner(tagline="updated")

        database_connection.rollback()
        assert get_learner(database_connection, "alice") is None


@pytest.mark.parametrize("handle", ["", ".", "..", "alice/bob", ".sync.lock", "bad\x00id"])
def test_learner_upsert_rejects_unsafe_handles(
    migrated_database_path: Path,
    handle: str,
) -> None:
    """Learner handles must be safe projection path components."""
    with (
        connect_database(migrated_database_path) as database_connection,
        pytest.raises(RepositoryError, match="unsafe learner handle"),
    ):
        upsert_learner(database_connection, learner(handle=handle))
