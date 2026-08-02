"""Tests for learner initialization CLI."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from maker_guide.cli import initialize_learner
from maker_guide.cli.initialize_learner import run
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.enrollment.models import EnrollmentServiceError
from maker_guide.repositories.cohort_membership import get_membership
from maker_guide.repositories.course_release import get_course_release
from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.learner import get_learner

if TYPE_CHECKING:
    import pytest


def test_initialize_learner_creates_learner_and_enrollment(
    migrated_database_path: Path,
) -> None:
    """The CLI initializes app state for a provisioned learner account."""
    assert (
        run(
            [
                "alice",
                "--database",
                str(migrated_database_path),
                "--joined-at",
                "2026-07-18T09:00:00Z",
                "--uid",
                "20001",
            ],
        )
        == 0
    )

    with connect_database(migrated_database_path) as database_connection:
        learner = get_learner(database_connection, "alice")
        membership = get_membership(database_connection, "alice", CATALOG.course.id)
        course_release = get_course_release(database_connection, CATALOG.course.id)

    assert learner is not None
    assert learner.joined_at == "2026-07-18T09:00:00Z"
    assert learner.uid == 20001
    assert membership is not None
    assert membership.joined_at == "2026-07-18T09:00:00Z"
    assert membership.rank_eligible is True
    assert course_release is None


def test_initialize_learner_is_idempotent(migrated_database_path: Path) -> None:
    """Re-running initialization keeps an existing learner enrolled."""
    arguments = [
        "alice",
        "--database",
        str(migrated_database_path),
        "--joined-at",
        "2026-07-18T09:00:00Z",
        "--uid",
        "20001",
    ]

    assert run(arguments) == 0
    assert run(arguments) == 0

    with connect_database(migrated_database_path) as database_connection:
        assert get_learner(database_connection, "alice") is not None
        membership = get_membership(database_connection, "alice", CATALOG.course.id)
        course_release = get_course_release(database_connection, CATALOG.course.id)

    assert membership is not None
    assert course_release is None


def test_initialize_learner_can_exclude_learner_from_rankings(
    migrated_database_path: Path,
) -> None:
    """The CLI persists explicit rank ineligibility."""
    assert (
        run(
            [
                "alice",
                "--database",
                str(migrated_database_path),
                "--joined-at",
                "2026-07-18T09:00:00Z",
                "--uid",
                "20001",
                "--not-rank-eligible",
            ],
        )
        == 0
    )

    with connect_database(migrated_database_path) as database_connection:
        membership = get_membership(database_connection, "alice", CATALOG.course.id)

    assert membership is not None
    assert membership.rank_eligible is False


def test_initialize_learner_creates_mentor_identity_without_enrollment(
    migrated_database_path: Path,
) -> None:
    """Mentors can use Guide without becoming course members."""
    assert (
        run(
            [
                "mentor",
                "--database",
                str(migrated_database_path),
                "--joined-at",
                "2026-07-18T09:00:00Z",
                "--uid",
                "10001",
                "--no-enroll",
            ],
        )
        == 0
    )

    with connect_database(migrated_database_path) as database_connection:
        learner = get_learner(database_connection, "mentor")
        membership = get_membership(database_connection, "mentor", CATALOG.course.id)

    assert learner is not None
    assert learner.uid == 10001
    assert membership is None


def test_initialize_learner_rolls_back_identity_when_enrollment_fails(
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed enrollment cannot leave a learner outside the course."""

    def fail_enrollment(*_arguments: object, **_keyword_arguments: object) -> None:
        raise EnrollmentServiceError("synthetic enrollment failure")

    monkeypatch.setattr(initialize_learner, "enroll", fail_enrollment)

    assert (
        run(
            [
                "alice",
                "--database",
                str(migrated_database_path),
                "--joined-at",
                "2026-07-18T09:00:00Z",
                "--uid",
                "10001",
            ],
        )
        == 1
    )

    with connect_database(migrated_database_path) as database_connection:
        assert get_learner(database_connection, "alice") is None
