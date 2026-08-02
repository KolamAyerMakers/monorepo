"""Tests for course enrollment service flows."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from maker_guide.enrollment.models import EnrollmentInput, EnrollmentServiceError
from maker_guide.enrollment.service import enroll
from maker_guide.identity.models import EnsureLearnerInput
from maker_guide.identity.service import ensure_learner
from maker_guide.repositories.audit_event import list_unexported_audit_events
from maker_guide.repositories.cohort_membership import get_membership
from maker_guide.repositories.course_release import (
    CourseRelease,
    get_course_release,
    upsert_course_release,
)
from maker_guide.repositories.helpers import connect_database, transaction
from maker_guide.repositories.outbox_item import list_pending_outbox_items
from tests.repositories.helpers import COURSE_ID, TIMESTAMP


def test_enroll_creates_membership_without_progress_placement(
    migrated_database_path: Path,
) -> None:
    """Enrollment creates course membership and leaves session progress unset."""
    with connect_database(migrated_database_path) as database_connection:
        ensure_learner(database_connection, _learner_input())

        first_result = enroll(database_connection, _enrollment_input())
        second_result = enroll(database_connection, _enrollment_input())

        assert first_result.created is True
        assert second_result.created is False
        assert second_result.membership == first_result.membership
        assert get_membership(database_connection, "alice", COURSE_ID) == first_result.membership
        assert first_result.membership.rank_eligible is True
        assert [
            event.event_type for event in list_unexported_audit_events(database_connection, 10)
        ] == ["learner_created", "cohort_enrolled"]
        assert list_unexported_audit_events(database_connection, 10)[1].payload == {
            "course_id": COURSE_ID,
            "rank_eligible": True,
        }
        assert [
            item.payload.get("reason")
            for item in list_pending_outbox_items(database_connection, 10)
        ] == ["learner_created", "enrollment"]


def test_enroll_does_not_overwrite_course_release(migrated_database_path: Path) -> None:
    """Re-enrollment is administrative and must not change the global release."""
    with connect_database(migrated_database_path) as database_connection:
        ensure_learner(database_connection, _learner_input())
        enroll(database_connection, _enrollment_input())
        course_release = CourseRelease(
            course_id=COURSE_ID,
            session_reached="S1",
            released_at=TIMESTAMP,
        )
        upsert_course_release(database_connection, course_release)

        enroll(database_connection, _enrollment_input())

        assert get_course_release(database_connection, COURSE_ID) == course_release


def test_enroll_persists_rank_ineligibility(migrated_database_path: Path) -> None:
    """Enrollment records the requested ranking eligibility."""
    with connect_database(migrated_database_path) as database_connection:
        ensure_learner(database_connection, _learner_input())

        result = enroll(database_connection, _enrollment_input(rank_eligible=False))

        assert result.membership.rank_eligible is False


def test_enroll_requires_existing_identity(migrated_database_path: Path) -> None:
    """Course enrollment cannot invent learner identity rows."""
    with (
        connect_database(migrated_database_path) as database_connection,
        pytest.raises(EnrollmentServiceError, match="identity does not exist"),
    ):
        enroll(database_connection, _enrollment_input())


def test_enroll_is_nested_transaction_safe(migrated_database_path: Path) -> None:
    """Enrollment writes roll back with an outer transaction."""
    with connect_database(migrated_database_path) as database_connection:
        ensure_learner(database_connection, _learner_input())
        with pytest.raises(RuntimeError, match="rollback outer transaction"):
            _enroll_then_raise(database_connection)

        assert get_membership(database_connection, "alice", COURSE_ID) is None
        assert [
            event.event_type for event in list_unexported_audit_events(database_connection, 10)
        ] == ["learner_created"]
        assert [
            item.payload.get("reason")
            for item in list_pending_outbox_items(database_connection, 10)
        ] == ["learner_created"]


def _enroll_then_raise(database_connection: sqlite3.Connection) -> None:
    with transaction(database_connection):
        enroll(database_connection, _enrollment_input())
        raise RuntimeError("rollback outer transaction")


def _learner_input() -> EnsureLearnerInput:
    return EnsureLearnerInput(handle="alice", joined_at=TIMESTAMP, source="chat")


def _enrollment_input(*, rank_eligible: bool = True) -> EnrollmentInput:
    return EnrollmentInput(
        handle="alice",
        course_id=COURSE_ID,
        joined_at=TIMESTAMP,
        source="chat",
        rank_eligible=rank_eligible,
    )
