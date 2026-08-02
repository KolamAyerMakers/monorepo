"""Outbox item repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Literal, cast

from maker_guide.repositories.helpers import (
    JsonPayload,
    RepositoryError,
    dump_json,
    last_inserted_id,
    load_json,
)

PROJECTION_OUTBOX_KIND = "projection"
GROUP_SYNC_OUTBOX_KIND = "group_sync"
PENDING_OUTBOX_STATUS = "pending"
FAILED_OUTBOX_STATUS = "failed"
PROCESSED_OUTBOX_STATUS = "processed"

type OutboxStatus = Literal["pending", "failed", "processed"]
type ProjectionOutboxReason = Literal[
    "learner_created",
    "enrollment",
    "course_released",
    "quest_assigned",
    "quest_completed",
    "session_objective_completed",
    "peer_thank_received",
]
type GroupSyncOutboxReason = Literal["group_grant_intended"]

_OUTBOX_STATUSES = frozenset(
    {PENDING_OUTBOX_STATUS, FAILED_OUTBOX_STATUS, PROCESSED_OUTBOX_STATUS},
)
_PROJECTION_OUTBOX_REASONS = frozenset(
    {
        "learner_created",
        "enrollment",
        "course_released",
        "quest_assigned",
        "quest_completed",
        "session_objective_completed",
        "peer_thank_received",
    },
)
_GROUP_SYNC_OUTBOX_REASONS = frozenset({"group_grant_intended"})
_PROJECTION_PAYLOAD_KEYS = frozenset({"handle", "course_id", "reason"})
_GROUP_SYNC_PAYLOAD_KEYS = frozenset({"handle", "course_id", "group_names", "reason"})


@dataclass(frozen=True, kw_only=True, slots=True)
class OutboxItem:
    """Queued non-transactional side effect."""

    id: int | None
    """SQLite-generated outbox id, absent before insert."""
    kind: str
    """Worker kind that should process this item."""
    status: OutboxStatus
    """Processing status for this item."""
    created_at: str
    """ISO timestamp for when this item was enqueued."""
    processed_at: str | None
    """ISO timestamp for when this item was processed."""
    payload: JsonPayload
    """Structured work item details."""


@dataclass(frozen=True, kw_only=True, slots=True)
class OutboxItemCount:
    """Count of outbox rows sharing one kind and status."""

    kind: str
    """Worker kind for these outbox rows."""
    status: str
    """Processing status for these outbox rows."""
    count: int
    """Number of rows with this kind and status."""


def enqueue_outbox_item(database_connection: sqlite3.Connection, item: OutboxItem) -> int:
    """Append an outbox item and return its id."""
    _validate_outbox_item_for_enqueue(item)
    return last_inserted_id(
        database_connection.execute(
            """
            insert into outbox_items (kind, status, created_at, processed_at, payload_json)
            values (?, ?, ?, ?, ?)
            """,
            (
                item.kind,
                item.status,
                item.created_at,
                item.processed_at,
                dump_json(item.payload),
            ),
        ),
    )


def projection_outbox_item(
    *,
    handle: str,
    created_at: str,
    reason: ProjectionOutboxReason,
    course_id: str | None = None,
) -> OutboxItem:
    """Construct a pending projection outbox item with a typed payload."""
    payload: JsonPayload = {"handle": handle, "reason": reason}
    if course_id is not None:
        payload["course_id"] = course_id
    return OutboxItem(
        id=None,
        kind=PROJECTION_OUTBOX_KIND,
        status=PENDING_OUTBOX_STATUS,
        created_at=created_at,
        processed_at=None,
        payload=payload,
    )


def group_sync_outbox_item(
    *,
    handle: str,
    course_id: str,
    group_names: tuple[str, ...],
    created_at: str,
    reason: GroupSyncOutboxReason = "group_grant_intended",
) -> OutboxItem:
    """Construct a pending Unix group-sync outbox item with a typed payload."""
    return OutboxItem(
        id=None,
        kind=GROUP_SYNC_OUTBOX_KIND,
        status=PENDING_OUTBOX_STATUS,
        created_at=created_at,
        processed_at=None,
        payload={
            "handle": handle,
            "course_id": course_id,
            "group_names": list(group_names),
            "reason": reason,
        },
    )


def validate_projection_outbox_item(item: OutboxItem) -> None:
    """Validate a projection outbox item before processing it."""
    if item.kind != PROJECTION_OUTBOX_KIND:
        raise RepositoryError(f"projection outbox item has wrong kind: {item.kind}")
    validate_projection_outbox_payload(item.payload)


def validate_group_sync_outbox_item(item: OutboxItem) -> None:
    """Validate a group-sync outbox item before processing it."""
    if item.kind != GROUP_SYNC_OUTBOX_KIND:
        raise RepositoryError(f"group sync outbox item has wrong kind: {item.kind}")
    validate_group_sync_outbox_payload(item.payload)


def validate_projection_outbox_payload(payload: JsonPayload) -> None:
    """Validate the JSON contract for a projection outbox payload."""
    _require_allowed_payload_keys(payload, _PROJECTION_PAYLOAD_KEYS, PROJECTION_OUTBOX_KIND)
    _require_string_field(payload, "handle", PROJECTION_OUTBOX_KIND)
    reason = _require_string_field(payload, "reason", PROJECTION_OUTBOX_KIND)
    if reason not in _PROJECTION_OUTBOX_REASONS:
        raise RepositoryError(f"projection outbox payload has invalid reason: {reason}")
    if reason != "learner_created":
        _require_string_field(payload, "course_id", PROJECTION_OUTBOX_KIND)
    if "course_id" in payload:
        _require_string_field(payload, "course_id", PROJECTION_OUTBOX_KIND)


def validate_group_sync_outbox_payload(payload: JsonPayload) -> None:
    """Validate the JSON contract for a group-sync outbox payload."""
    _require_allowed_payload_keys(payload, _GROUP_SYNC_PAYLOAD_KEYS, GROUP_SYNC_OUTBOX_KIND)
    _require_string_field(payload, "handle", GROUP_SYNC_OUTBOX_KIND)
    _require_string_field(payload, "course_id", GROUP_SYNC_OUTBOX_KIND)
    reason = _require_string_field(payload, "reason", GROUP_SYNC_OUTBOX_KIND)
    if reason not in _GROUP_SYNC_OUTBOX_REASONS:
        raise RepositoryError(f"group sync outbox payload has invalid reason: {reason}")
    _require_string_list_field(payload, "group_names", GROUP_SYNC_OUTBOX_KIND)


def list_pending_outbox_items(
    database_connection: sqlite3.Connection,
    limit: int,
) -> list[OutboxItem]:
    """Return pending outbox items in creation order."""
    item_records = cast(
        "list[tuple[int, str, str, str, str | None, str]]",
        database_connection.execute(
            """
            select id, kind, status, created_at, processed_at, payload_json
            from outbox_items
            where status = ?
            order by created_at, id
            limit ?
            """,
            (PENDING_OUTBOX_STATUS, limit),
        ).fetchall(),
    )
    return [_outbox_item_from_record(item_record) for item_record in item_records]


def list_pending_outbox_items_by_kind(
    database_connection: sqlite3.Connection,
    kind: str,
    limit: int,
) -> list[OutboxItem]:
    """Return pending outbox items for one worker kind in creation order."""
    item_records = cast(
        "list[tuple[int, str, str, str, str | None, str]]",
        database_connection.execute(
            """
            select id, kind, status, created_at, processed_at, payload_json
            from outbox_items
            where status = ? and kind = ?
            order by created_at, id
            limit ?
            """,
            (PENDING_OUTBOX_STATUS, kind, limit),
        ).fetchall(),
    )
    return [_outbox_item_from_record(item_record) for item_record in item_records]


def list_retryable_outbox_items_by_kind(
    database_connection: sqlite3.Connection,
    kind: str,
    limit: int,
) -> list[OutboxItem]:
    """Return pending or failed outbox items for one worker kind."""
    item_records = cast(
        "list[tuple[int, str, str, str, str | None, str]]",
        database_connection.execute(
            """
            select id, kind, status, created_at, processed_at, payload_json
            from outbox_items
            where status in (?, ?) and kind = ?
            order by created_at, id
            limit ?
            """,
            (PENDING_OUTBOX_STATUS, FAILED_OUTBOX_STATUS, kind, limit),
        ).fetchall(),
    )
    return [_outbox_item_from_record(item_record) for item_record in item_records]


def list_retryable_outbox_item_ids_by_kind(
    database_connection: sqlite3.Connection,
    kind: str,
    limit: int,
) -> tuple[int, ...]:
    """Return ids for pending or failed outbox items without decoding payloads."""
    item_id_records = cast(
        "list[tuple[int]]",
        database_connection.execute(
            """
            select id
            from outbox_items
            where status in (?, ?) and kind = ?
            order by created_at, id
            limit ?
            """,
            (PENDING_OUTBOX_STATUS, FAILED_OUTBOX_STATUS, kind, limit),
        ).fetchall(),
    )
    return tuple(item_id_record[0] for item_id_record in item_id_records)


def count_outbox_items_by_kind_and_status(
    database_connection: sqlite3.Connection,
) -> list[OutboxItemCount]:
    """Return outbox row counts grouped by worker kind and status."""
    count_records = cast(
        "list[tuple[str, str, int]]",
        database_connection.execute(
            """
            select kind, status, count(*)
            from outbox_items
            group by kind, status
            order by kind, status
            """,
        ).fetchall(),
    )
    return [
        OutboxItemCount(
            kind=count_record[0],
            status=count_record[1],
            count=count_record[2],
        )
        for count_record in count_records
    ]


def mark_outbox_item_processed(
    database_connection: sqlite3.Connection,
    item_id: int,
    processed_at: str,
) -> None:
    """Mark an outbox item as processed."""
    database_connection.execute(
        """
        update outbox_items
        set status = ?, processed_at = ?
        where id = ?
        """,
        (PROCESSED_OUTBOX_STATUS, processed_at, item_id),
    )


def mark_outbox_item_failed(database_connection: sqlite3.Connection, item_id: int) -> None:
    """Mark an outbox item failed so workers can retry it later."""
    database_connection.execute(
        """
        update outbox_items
        set status = ?, processed_at = null
        where id = ?
        """,
        (FAILED_OUTBOX_STATUS, item_id),
    )


def _outbox_item_from_record(item_record: tuple[int, str, str, str, str | None, str]) -> OutboxItem:
    return OutboxItem(
        id=item_record[0],
        kind=item_record[1],
        status=_outbox_status_from_value(item_record[2]),
        created_at=item_record[3],
        processed_at=item_record[4],
        payload=load_json(item_record[5]),
    )


def _validate_outbox_item_for_enqueue(item: OutboxItem) -> None:
    _outbox_status_from_value(item.status)
    match item.kind:
        case kind if kind == PROJECTION_OUTBOX_KIND:
            validate_projection_outbox_payload(item.payload)
        case kind if kind == GROUP_SYNC_OUTBOX_KIND:
            validate_group_sync_outbox_payload(item.payload)
        case _:
            pass


def _outbox_status_from_value(status: str) -> OutboxStatus:
    if status not in _OUTBOX_STATUSES:
        raise RepositoryError(f"invalid outbox status: {status}")
    return cast("OutboxStatus", status)


def _require_allowed_payload_keys(
    payload: JsonPayload,
    allowed_keys: frozenset[str],
    kind: str,
) -> None:
    unexpected_keys = sorted(payload.keys() - allowed_keys)
    if unexpected_keys:
        raise RepositoryError(
            f"{kind} outbox payload has unexpected keys: {', '.join(unexpected_keys)}",
        )


def _require_string_field(payload: JsonPayload, field_name: str, kind: str) -> str:
    field_value = payload.get(field_name)
    if not isinstance(field_value, str):
        raise RepositoryError(f"{kind} outbox payload field is not a string: {field_name}")
    return field_value


def _require_string_list_field(payload: JsonPayload, field_name: str, kind: str) -> tuple[str, ...]:
    field_value = payload.get(field_name)
    if not isinstance(field_value, list):
        raise RepositoryError(f"{kind} outbox payload field is not a string list: {field_name}")
    field_items = cast("list[object]", field_value)
    if not all(isinstance(field_item, str) for field_item in field_items):
        raise RepositoryError(f"{kind} outbox payload field is not a string list: {field_name}")
    return tuple(field_item for field_item in field_items if isinstance(field_item, str))
