"""Tests for outbox item repository functions."""

from __future__ import annotations

from pathlib import Path

import pytest

from maker_guide.repositories.helpers import RepositoryError, connect_database
from maker_guide.repositories.outbox_item import (
    GROUP_SYNC_OUTBOX_KIND,
    PENDING_OUTBOX_STATUS,
    PROJECTION_OUTBOX_KIND,
    OutboxItem,
    enqueue_outbox_item,
    group_sync_outbox_item,
    list_pending_outbox_items,
    list_pending_outbox_items_by_kind,
    list_retryable_outbox_items_by_kind,
    mark_outbox_item_failed,
    mark_outbox_item_processed,
    projection_outbox_item,
)
from tests.repositories.helpers import COURSE_ID, TIMESTAMP


def test_outbox_item_lists_pending_items(migrated_database_path: Path) -> None:
    """Processed outbox items are excluded from pending queries."""
    with connect_database(migrated_database_path) as database_connection:
        first_outbox_id = enqueue_outbox_item(
            database_connection,
            _outbox_item(kind=PROJECTION_OUTBOX_KIND, created_at=TIMESTAMP),
        )
        enqueue_outbox_item(
            database_connection,
            _outbox_item(kind="irc", created_at="2026-07-11T09:02:00Z"),
        )

        mark_outbox_item_processed(
            database_connection,
            first_outbox_id,
            "2026-07-11T09:03:00Z",
        )

        assert [item.kind for item in list_pending_outbox_items(database_connection, limit=10)] == [
            "irc",
        ]


def test_outbox_item_lists_pending_items_by_kind(migrated_database_path: Path) -> None:
    """Workers can fetch only the pending items for their kind."""
    with connect_database(migrated_database_path) as database_connection:
        enqueue_outbox_item(
            database_connection,
            _outbox_item(kind=PROJECTION_OUTBOX_KIND, created_at=TIMESTAMP),
        )
        enqueue_outbox_item(
            database_connection,
            _outbox_item(kind="irc", created_at="2026-07-11T09:02:00Z"),
        )

        assert [
            item.kind
            for item in list_pending_outbox_items_by_kind(
                database_connection,
                PROJECTION_OUTBOX_KIND,
                10,
            )
        ] == [PROJECTION_OUTBOX_KIND]


def test_outbox_item_lists_failed_items_as_retryable(migrated_database_path: Path) -> None:
    """Failed rows remain retryable, processed rows do not."""
    with connect_database(migrated_database_path) as database_connection:
        failed_outbox_id = enqueue_outbox_item(
            database_connection,
            _outbox_item(kind=PROJECTION_OUTBOX_KIND, created_at=TIMESTAMP),
        )
        processed_outbox_id = enqueue_outbox_item(
            database_connection,
            _outbox_item(kind=PROJECTION_OUTBOX_KIND, created_at="2026-07-11T09:02:00Z"),
        )
        enqueue_outbox_item(
            database_connection,
            _outbox_item(kind="irc", created_at="2026-07-11T09:03:00Z"),
        )

        mark_outbox_item_failed(database_connection, failed_outbox_id)
        mark_outbox_item_processed(
            database_connection,
            processed_outbox_id,
            "2026-07-11T09:04:00Z",
        )

        assert [
            item.status
            for item in list_retryable_outbox_items_by_kind(
                database_connection,
                PROJECTION_OUTBOX_KIND,
                10,
            )
        ] == ["failed"]


@pytest.mark.parametrize(
    ("outbox_item", "message"),
    [
        (
            OutboxItem(
                id=None,
                kind=PROJECTION_OUTBOX_KIND,
                status=PENDING_OUTBOX_STATUS,
                created_at=TIMESTAMP,
                processed_at=None,
                payload={"handle": "alice"},
            ),
            "projection outbox payload",
        ),
        (
            OutboxItem(
                id=None,
                kind=GROUP_SYNC_OUTBOX_KIND,
                status=PENDING_OUTBOX_STATUS,
                created_at=TIMESTAMP,
                processed_at=None,
                payload={"handle": "alice", "reason": "group_grant_intended"},
            ),
            "group_sync outbox payload",
        ),
    ],
)
def test_enqueue_outbox_item_rejects_malformed_production_payloads(
    migrated_database_path: Path,
    outbox_item: OutboxItem,
    message: str,
) -> None:
    """Production outbox kinds must satisfy their payload contract at enqueue."""
    with (
        connect_database(migrated_database_path) as database_connection,
        pytest.raises(RepositoryError, match=message),
    ):
        enqueue_outbox_item(database_connection, outbox_item)


def _outbox_item(kind: str, created_at: str) -> OutboxItem:
    match kind:
        case matched_kind if matched_kind == PROJECTION_OUTBOX_KIND:
            return projection_outbox_item(
                handle="alice",
                course_id=COURSE_ID,
                created_at=created_at,
                reason="enrollment",
            )
        case matched_kind if matched_kind == GROUP_SYNC_OUTBOX_KIND:
            return group_sync_outbox_item(
                handle="alice",
                course_id=COURSE_ID,
                group_names=(COURSE_ID,),
                created_at=created_at,
            )
        case _:
            return OutboxItem(
                id=None,
                kind=kind,
                status=PENDING_OUTBOX_STATUS,
                created_at=created_at,
                processed_at=None,
                payload={"handle": "alice"},
            )
