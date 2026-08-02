"""Tests for identity service flows."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from maker_guide.identity.models import EnsureLearnerInput
from maker_guide.identity.service import ensure_learner
from maker_guide.repositories.audit_event import list_unexported_audit_events
from maker_guide.repositories.helpers import RepositoryError, connect_database, transaction
from maker_guide.repositories.learner import get_learner
from maker_guide.repositories.outbox_item import list_pending_outbox_items
from tests.repositories.helpers import TIMESTAMP


def test_ensure_learner_creates_identity_audit_and_projection(
    migrated_database_path: Path,
) -> None:
    """Ensuring a new learner creates identity state exactly once."""
    with connect_database(migrated_database_path) as database_connection:
        first_result = ensure_learner(database_connection, _learner_input(tagline="ready"))
        second_result = ensure_learner(database_connection, _learner_input(tagline="ignored"))

        assert first_result.created is True
        assert second_result.created is False
        assert second_result.learner == first_result.learner
        assert get_learner(database_connection, "alice") == first_result.learner
        assert [
            event.event_type for event in list_unexported_audit_events(database_connection, 10)
        ] == ["learner_created"]
        assert [item.payload for item in list_pending_outbox_items(database_connection, 10)] == [
            {"handle": "alice", "reason": "learner_created"},
        ]


def test_ensure_learner_is_nested_transaction_safe(migrated_database_path: Path) -> None:
    """Identity writes roll back with an outer transaction."""
    with connect_database(migrated_database_path) as database_connection:
        with pytest.raises(RuntimeError, match="rollback outer transaction"):
            _ensure_learner_then_raise(database_connection)

        assert get_learner(database_connection, "alice") is None
        assert list_unexported_audit_events(database_connection, 10) == []
        assert list_pending_outbox_items(database_connection, 10) == []


def test_ensure_learner_rejects_unsafe_handle(migrated_database_path: Path) -> None:
    """Identity creation rejects handles that would poison projections."""
    with connect_database(migrated_database_path) as database_connection:
        with pytest.raises(RepositoryError, match="unsafe learner handle"):
            ensure_learner(database_connection, _learner_input(tagline="ready", handle="../bad"))

        assert get_learner(database_connection, "../bad") is None
        assert list_unexported_audit_events(database_connection, 10) == []
        assert list_pending_outbox_items(database_connection, 10) == []


def _ensure_learner_then_raise(database_connection: sqlite3.Connection) -> None:
    with transaction(database_connection):
        ensure_learner(database_connection, _learner_input(tagline="ready"))
        raise RuntimeError("rollback outer transaction")


def _learner_input(tagline: str, handle: str = "alice") -> EnsureLearnerInput:
    return EnsureLearnerInput(
        handle=handle,
        joined_at=TIMESTAMP,
        source="chat",
        tagline=tagline,
    )
