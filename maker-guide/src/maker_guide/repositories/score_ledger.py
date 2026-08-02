"""Score ledger repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast

from maker_guide.repositories.helpers import RepositoryError, last_inserted_id


@dataclass(frozen=True, kw_only=True, slots=True)
class ScoreLedgerEntry:
    """Append-only score ledger entry."""

    id: int | None
    """SQLite-generated ledger id, absent before insert."""
    handle: str
    """Shared learner id."""
    course_id: str
    """Course id from the Python curriculum catalog."""
    amount: int
    """Score delta for this ledger entry."""
    reason: str
    """Deterministic reason for the score change."""
    related_type: str | None
    """Optional type of related source object."""
    related_id: str | None
    """Optional id of related source object."""
    created_at: str
    """ISO timestamp for when the ledger entry was created."""


def add_score_entry(database_connection: sqlite3.Connection, entry: ScoreLedgerEntry) -> int:
    """Append a score ledger entry, idempotently for uniquely constrained awards."""
    _validate_score_entry(entry)
    insert_cursor = database_connection.execute(
        """
        insert or ignore into score_ledger
            (handle, course_id, amount, reason, related_type, related_id, created_at)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry.handle,
            entry.course_id,
            entry.amount,
            entry.reason,
            entry.related_type,
            entry.related_id,
            entry.created_at,
        ),
    )
    if insert_cursor.rowcount == 1:
        return last_inserted_id(insert_cursor)
    existing_entry_id = _get_existing_score_entry_id(database_connection, entry)
    if existing_entry_id is None:
        raise RepositoryError("score ledger insert was ignored without an existing entry")
    return existing_entry_id


def _validate_score_entry(entry: ScoreLedgerEntry) -> None:
    if entry.reason == "quest_completed" and (
        entry.related_type != "quest" or entry.related_id is None
    ):
        raise RepositoryError("quest completion score requires a quest related id")
    if entry.reason == "peer_thank_received" and (
        entry.related_type != "peer_thank" or entry.related_id is None
    ):
        raise RepositoryError("peer thank score requires a thank related id")
    if entry.reason == "quest_completion_speed_bonus" and (
        entry.related_type != "quest" or entry.related_id is None
    ):
        raise RepositoryError("quest speed bonus requires a quest related id")
    if entry.reason in {"session_objective_completed", "session_objective_speed_bonus"} and (
        entry.related_type != "session_objective" or entry.related_id is None
    ):
        raise RepositoryError("session objective score requires an objective related id")


def _get_existing_score_entry_id(
    database_connection: sqlite3.Connection,
    entry: ScoreLedgerEntry,
) -> int | None:
    entry_record = cast(
        "tuple[int, int] | None",
        database_connection.execute(
            """
            select id, amount
            from score_ledger
            where handle = ?
                and course_id = ?
                and reason = ?
                and related_type = ?
                and related_id = ?
            """,
            (
                entry.handle,
                entry.course_id,
                entry.reason,
                entry.related_type,
                entry.related_id,
            ),
        ).fetchone(),
    )
    if entry_record is None:
        return None
    if entry_record[1] != entry.amount:
        raise RepositoryError("conflicting score ledger entry already exists")
    return entry_record[0]


def total_score_for_course(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
) -> int:
    """Return total score for a learner course."""
    total_record = cast(
        "tuple[int | None]",
        database_connection.execute(
            "select sum(amount) from score_ledger where handle = ? and course_id = ?",
            (handle, course_id),
        ).fetchone(),
    )
    return total_record[0] or 0


def list_score_entries(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
) -> list[ScoreLedgerEntry]:
    """Return score ledger entries for a learner course."""
    entry_records = cast(
        "list[tuple[int, str, str, int, str, str | None, str | None, str]]",
        database_connection.execute(
            """
            select id, handle, course_id, amount, reason, related_type, related_id, created_at
            from score_ledger
            where handle = ? and course_id = ?
            order by created_at, id
            """,
            (handle, course_id),
        ).fetchall(),
    )
    return [
        ScoreLedgerEntry(
            id=entry_record[0],
            handle=entry_record[1],
            course_id=entry_record[2],
            amount=entry_record[3],
            reason=entry_record[4],
            related_type=entry_record[5],
            related_id=entry_record[6],
            created_at=entry_record[7],
        )
        for entry_record in entry_records
    ]
