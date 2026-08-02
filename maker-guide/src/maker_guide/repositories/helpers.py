"""Shared helpers for SQLite repositories."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import cast

JsonPayload = dict[str, object]
_SAVEPOINT_NAME = "maker_guide_nested_transaction"
DATABASE_FILE_MODE = 0o640


class RepositoryError(RuntimeError):
    """Raised when repository data cannot be mapped safely."""


def connect_database(database_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection with foreign-key enforcement enabled."""
    database_connection = sqlite3.connect(database_path)
    try:
        ensure_database_file_permissions(database_path)
        database_connection.execute("pragma foreign_keys = on")
    except BaseException:
        database_connection.close()
        raise
    else:
        return database_connection


def ensure_database_file_permissions(database_path: Path) -> None:
    """Keep SQLite state databases readable only by the owner and group."""
    if database_path.stat().st_mode & 0o777 != DATABASE_FILE_MODE:
        database_path.chmod(DATABASE_FILE_MODE)


@contextmanager
def transaction(database_connection: sqlite3.Connection) -> Generator[None]:
    """Commit at the outer boundary and use savepoints inside active transactions."""
    if database_connection.in_transaction:
        database_connection.execute(f"savepoint {_SAVEPOINT_NAME}")
        try:
            yield
        except BaseException:
            database_connection.execute(f"rollback to savepoint {_SAVEPOINT_NAME}")
            database_connection.execute(f"release savepoint {_SAVEPOINT_NAME}")
            raise
        else:
            database_connection.execute(f"release savepoint {_SAVEPOINT_NAME}")
        return

    database_connection.execute("begin")
    try:
        yield
    except BaseException:
        database_connection.rollback()
        raise
    else:
        database_connection.commit()


def last_inserted_id(cursor: sqlite3.Cursor) -> int:
    """Return the SQLite row id from an insert cursor."""
    if cursor.lastrowid is None:
        raise RepositoryError("insert did not produce a row id")
    return cursor.lastrowid


def dump_json(payload: JsonPayload) -> str:
    """Serialize a JSON object payload deterministically."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def load_json(payload_json: str) -> JsonPayload:
    """Deserialize a JSON object payload."""
    payload = cast("object", json.loads(payload_json))
    if isinstance(payload, dict):
        payload_mapping = cast("dict[object, object]", payload)
        if all(isinstance(key, str) for key in payload_mapping):
            return {key: value for key, value in payload_mapping.items() if isinstance(key, str)}
    raise RepositoryError("JSON payload must be an object")


def topic_tags_from_json(payload_json: str) -> tuple[str, ...]:
    """Deserialize help interaction topic tags."""
    payload = load_json(payload_json)
    tags = payload.get("tags")
    if isinstance(tags, list):
        tag_objects = cast("list[object]", tags)
        if all(isinstance(tag_object, str) for tag_object in tag_objects):
            return tuple(tag_object for tag_object in tag_objects if isinstance(tag_object, str))
    raise RepositoryError("help interaction topic tags must be a string list")
