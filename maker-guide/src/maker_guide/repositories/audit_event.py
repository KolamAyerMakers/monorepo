"""Audit event repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast

from maker_guide.repositories.helpers import JsonPayload, dump_json, last_inserted_id, load_json


@dataclass(frozen=True, kw_only=True, slots=True)
class AuditEvent:
    """Committed audit event awaiting optional JSONL export."""

    id: int | None = None
    """SQLite-generated audit id, absent before insert."""
    event_type: str
    """Audit event type."""
    handle: str | None
    """Shared learner id, if the event is learner-scoped."""
    source: str
    """Actor or subsystem that created the event."""
    created_at: str
    """ISO timestamp for when the audit event was created."""
    payload: JsonPayload
    """Structured audit event details."""
    exported_at: str | None = None
    """ISO timestamp for when the event was exported to JSONL."""


def append_audit_event(database_connection: sqlite3.Connection, event: AuditEvent) -> int:
    """Append an audit event and return its id."""
    return last_inserted_id(
        database_connection.execute(
            """
            insert into audit_events
                (event_type, handle, source, created_at, payload_json, exported_at)
            values (?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_type,
                event.handle,
                event.source,
                event.created_at,
                dump_json(event.payload),
                event.exported_at,
            ),
        ),
    )


def list_unexported_audit_events(
    database_connection: sqlite3.Connection,
    limit: int,
) -> list[AuditEvent]:
    """Return unexported audit events in commit order."""
    event_records = cast(
        "list[tuple[int, str, str | None, str, str, str, str | None]]",
        database_connection.execute(
            """
            select id, event_type, handle, source, created_at, payload_json, exported_at
            from audit_events
            where exported_at is null
            order by id
            limit ?
            """,
            (limit,),
        ).fetchall(),
    )
    return [_audit_event_from_record(event_record) for event_record in event_records]


def list_recent_audit_events_by_type(  # noqa: PLR0913 - Query scope and time bounds are explicit.
    database_connection: sqlite3.Connection,
    event_type: str,
    handle: str,
    created_since: str,
    limit: int,
    *,
    created_through: str | None = None,
) -> list[AuditEvent]:
    """Return recent learner-scoped audit events for deterministic validation."""
    event_records = cast(
        "list[tuple[int, str, str | None, str, str, str, str | None]]",
        database_connection.execute(
            """
            select id, event_type, handle, source, created_at, payload_json, exported_at
            from audit_events
            where event_type = ?
                and handle = ?
                and created_at >= ?
                and (? is null or created_at <= ?)
            order by id desc
            limit ?
            """,
            (event_type, handle, created_since, created_through, created_through, limit),
        ).fetchall(),
    )
    return [_audit_event_from_record(event_record) for event_record in event_records]


def count_unexported_audit_events(database_connection: sqlite3.Connection) -> int:
    """Return the number of audit rows still awaiting JSONL export."""
    return cast(
        "tuple[int]",
        database_connection.execute(
            "select count(*) from audit_events where exported_at is null",
        ).fetchone(),
    )[0]


def mark_audit_event_exported(
    database_connection: sqlite3.Connection,
    event_id: int,
    exported_at: str,
) -> None:
    """Mark an audit event as exported."""
    database_connection.execute(
        "update audit_events set exported_at = ? where id = ?",
        (exported_at, event_id),
    )


def _audit_event_from_record(
    event_record: tuple[int, str, str | None, str, str, str, str | None],
) -> AuditEvent:
    return AuditEvent(
        id=event_record[0],
        event_type=event_record[1],
        handle=event_record[2],
        source=event_record[3],
        created_at=event_record[4],
        payload=load_json(event_record[5]),
        exported_at=event_record[6],
    )
