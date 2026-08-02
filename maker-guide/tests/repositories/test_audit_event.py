"""Tests for audit event repository functions."""

from __future__ import annotations

from pathlib import Path

from maker_guide.repositories.audit_event import (
    AuditEvent,
    append_audit_event,
    list_unexported_audit_events,
    mark_audit_event_exported,
)
from maker_guide.repositories.helpers import connect_database
from tests.repositories.helpers import COURSE_ID, TIMESTAMP, write_learner


def test_audit_event_lists_unexported_events(migrated_database_path: Path) -> None:
    """Exported audit events are excluded from unexported queries."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        first_audit_id = append_audit_event(database_connection, _audit_event("learner_created"))
        second_audit_id = append_audit_event(database_connection, _audit_event("score_awarded"))

        mark_audit_event_exported(
            database_connection,
            first_audit_id,
            "2026-07-11T09:03:00Z",
        )

        assert [
            event.id for event in list_unexported_audit_events(database_connection, limit=10)
        ] == [second_audit_id]


def _audit_event(event_type: str) -> AuditEvent:
    return AuditEvent(
        id=None,
        event_type=event_type,
        handle="alice",
        source="test",
        created_at=TIMESTAMP,
        payload={"course_id": COURSE_ID},
        exported_at=None,
    )
