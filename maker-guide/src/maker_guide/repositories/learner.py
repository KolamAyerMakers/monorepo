"""Learner repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast

from maker_guide.repositories.helpers import RepositoryError

_RESERVED_LEARNER_HANDLES = frozenset({".sync.lock"})


@dataclass(frozen=True, kw_only=True, slots=True)
class Learner:
    """Learner account state."""

    handle: str
    """Shared learner id across Unix, IRC, and course state."""
    joined_at: str
    """ISO timestamp for when the learner joined."""
    tagline: str | None
    """Optional learner-controlled profile text."""
    created_at: str
    """ISO timestamp for when this row was created."""
    uid: int | None = None
    """Immutable POSIX uid used to route the learner's web service."""


def upsert_learner(database_connection: sqlite3.Connection, learner: Learner) -> None:
    """Insert or update a learner."""
    validate_learner_handle(learner.handle)
    database_connection.execute(
        """
        insert into learners (handle, joined_at, tagline, created_at, uid)
        values (?, ?, ?, ?, ?)
        on conflict(handle) do update set
            joined_at = excluded.joined_at,
            tagline = excluded.tagline,
            created_at = excluded.created_at,
            uid = coalesce(learners.uid, excluded.uid)
        """,
        (learner.handle, learner.joined_at, learner.tagline, learner.created_at, learner.uid),
    )


def validate_learner_handle(handle: str) -> None:
    """Reject learner handles that cannot be safe projection path components."""
    if not is_safe_learner_handle(handle):
        raise RepositoryError(f"unsafe learner handle: {handle}")


def is_safe_learner_handle(handle: str) -> bool:
    """Return whether a learner handle is safe as one projection path component."""
    return (
        handle not in {"", ".", ".."}
        and "/" not in handle
        and "\x00" not in handle
        and handle not in _RESERVED_LEARNER_HANDLES
    )


def get_learner(database_connection: sqlite3.Connection, handle: str) -> Learner | None:
    """Return a learner by handle."""
    learner_record = cast(
        "tuple[str, str, str | None, str, int | None] | None",
        database_connection.execute(
            "select handle, joined_at, tagline, created_at, uid from learners where handle = ?",
            (handle,),
        ).fetchone(),
    )
    if learner_record is None:
        return None
    return Learner(
        handle=learner_record[0],
        joined_at=learner_record[1],
        tagline=learner_record[2],
        created_at=learner_record[3],
        uid=learner_record[4],
    )


def list_learners(database_connection: sqlite3.Connection) -> list[Learner]:
    """Return learners in deterministic handle order."""
    learner_records = cast(
        "list[tuple[str, str, str | None, str, int | None]]",
        database_connection.execute(
            "select handle, joined_at, tagline, created_at, uid from learners order by handle",
        ).fetchall(),
    )
    return [
        Learner(
            handle=learner_record[0],
            joined_at=learner_record[1],
            tagline=learner_record[2],
            created_at=learner_record[3],
            uid=learner_record[4],
        )
        for learner_record in learner_records
    ]
