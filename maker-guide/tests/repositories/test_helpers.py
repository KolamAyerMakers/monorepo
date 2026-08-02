"""Tests for shared SQLite repository helpers."""

from __future__ import annotations

import os
from pathlib import Path

from maker_guide.repositories.helpers import DATABASE_FILE_MODE, connect_database


def test_connect_database_creates_group_readable_state_file(temporary_path: Path) -> None:
    """Application-created SQLite files are readable by the deployment group."""
    database_path = temporary_path / "state.db"
    previous_umask = os.umask(0)
    try:
        with connect_database(database_path):
            pass
    finally:
        os.umask(previous_umask)

    assert database_path.stat().st_mode & 0o777 == DATABASE_FILE_MODE


def test_connect_database_leaves_correct_permissions_alone(temporary_path: Path) -> None:
    """Correctly managed SQLite files are usable by non-owner readers."""
    database_path = temporary_path / "state.db"
    database_path.touch(mode=DATABASE_FILE_MODE)

    with connect_database(database_path):
        pass

    assert database_path.stat().st_mode & 0o777 == DATABASE_FILE_MODE
