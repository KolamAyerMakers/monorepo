"""Tests for transactional progress service flows."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import cast

import pytest

from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.curriculum.models import Quest
from maker_guide.enrollment.models import EnrollmentInput
from maker_guide.enrollment.service import enroll
from maker_guide.identity.models import EnsureLearnerInput
from maker_guide.identity.service import ensure_learner
from maker_guide.progress.models import (
    CourseReleaseInput,
    ProgressServiceError,
    QuestAttemptInput,
    QuestAttemptOutcome,
    QuestCompletionInput,
    QuestCompletionResult,
)
from maker_guide.progress.service import (
    complete_quest,
    complete_session_objective,
    current_quest,
    current_session_objective,
    record_attempt,
    release_course,
)
from maker_guide.repositories.audit_event import list_unexported_audit_events
from maker_guide.repositories.course_release import get_course_release
from maker_guide.repositories.helpers import RepositoryError, connect_database
from maker_guide.repositories.outbox_item import list_pending_outbox_items
from maker_guide.repositories.quest_assignment import QuestAssignment, assign_quest, get_assignment
from maker_guide.repositories.quest_attempt import QuestAttempt, record_quest_attempt
from maker_guide.repositories.quest_completion import (
    QuestCompletion,
    get_quest_completion,
    list_quest_completions,
)
from maker_guide.repositories.quest_completion import complete_quest as write_quest_completion
from maker_guide.repositories.score_ledger import (
    ScoreLedgerEntry,
    add_score_entry,
    list_score_entries,
    total_score_for_course,
)
from maker_guide.repositories.session_objective_completion import (
    SessionObjectiveCompletion,
    list_completed_objective_ids,
)
from maker_guide.repositories.session_objective_completion import (
    complete_session_objective as write_session_objective_completion,
)
from maker_guide.repositories.tier_promotion import list_tier_promotions

HANDLE = "alice"
JOINED_AT = "2026-07-18T09:00:00Z"
SOURCE = "chat"


def test_release_course_rejects_skipped_sessions_before_writes(
    migrated_database_path: Path,
) -> None:
    """Neither an initial S10 release nor an S1-to-S3 jump mutates release state."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll_without_session_placement(database_connection)
        initial_audit_events = list_unexported_audit_events(database_connection, 10)
        initial_outbox_items = list_pending_outbox_items(database_connection, 10)

        with pytest.raises(ProgressServiceError, match="one at a time"):
            release_course(
                database_connection,
                CATALOG,
                CourseReleaseInput(
                    session_reached="S10",
                    updated_at="2026-07-18T08:00:00Z",
                    source=SOURCE,
                ),
            )

        assert get_course_release(database_connection, CATALOG.course.id) is None
        assert list_unexported_audit_events(database_connection, 10) == initial_audit_events
        assert list_pending_outbox_items(database_connection, 10) == initial_outbox_items

        release_course(
            database_connection,
            CATALOG,
            CourseReleaseInput(
                session_reached="S1",
                updated_at=JOINED_AT,
                source=SOURCE,
            ),
        )
        audit_events = list_unexported_audit_events(database_connection, 10)
        outbox_items = list_pending_outbox_items(database_connection, 10)

        with pytest.raises(ProgressServiceError, match="one at a time"):
            release_course(
                database_connection,
                CATALOG,
                CourseReleaseInput(
                    session_reached="S3",
                    updated_at="2026-08-01T09:00:00Z",
                    source=SOURCE,
                ),
            )

        course_release = get_course_release(database_connection, CATALOG.course.id)
        assert course_release is not None
        assert course_release.session_reached == "S1"
        assert list_unexported_audit_events(database_connection, 10) == audit_events
        assert list_pending_outbox_items(database_connection, 10) == outbox_items


def test_current_quest_requires_session_placement(migrated_database_path: Path) -> None:
    """Enrollment alone is not enough to assign progress-gated quests."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll_without_session_placement(database_connection)

        with pytest.raises(ProgressServiceError, match="has not reached"):
            current_quest(
                database_connection,
                CATALOG,
                handle=HANDLE,
                assigned_at="2026-07-19T09:00:00Z",
                source=SOURCE,
            )


def test_current_quest_assigns_before_returning(migrated_database_path: Path) -> None:
    """The current quest service persists an assignment before returning it."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        first_result = current_quest(
            database_connection,
            CATALOG,
            handle=HANDLE,
            assigned_at="2026-07-19T09:00:00Z",
            source=SOURCE,
        )
        second_result = current_quest(
            database_connection,
            CATALOG,
            handle=HANDLE,
            assigned_at="2026-07-19T09:01:00Z",
            source=SOURCE,
        )

        assert first_result.quest == CATALOG.course.quests[0]
        assert first_result.assignment == get_assignment(
            database_connection,
            HANDLE,
            CATALOG.course.id,
            CATALOG.course.quests[0].id,
        )
        assert first_result.assigned_now is True
        assert second_result.quest == first_result.quest
        assert second_result.assignment == first_result.assignment
        assert second_result.assigned_now is False


def test_current_quest_waits_for_every_released_objective(
    migrated_database_path: Path,
) -> None:
    """Completing one S3 objective cannot assign its first follow-up quest."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        _write_completed_session_objectives(database_connection, "S2")
        release_course(
            database_connection,
            CATALOG,
            CourseReleaseInput(
                session_reached="S2",
                updated_at="2026-07-25T09:00:00Z",
                source=SOURCE,
            ),
        )
        release_course(
            database_connection,
            CATALOG,
            CourseReleaseInput(
                session_reached="S3",
                updated_at="2026-08-01T09:00:00Z",
                source=SOURCE,
            ),
        )
        complete_session_objective(
            database_connection,
            CATALOG,
            handle=HANDLE,
            session_id="S3",
            objective_id="separate-standard-streams",
            completed_at="2026-08-01T09:01:00Z",
            evidence={"passed": True},
        )

        objective_result = current_session_objective(
            database_connection,
            CATALOG,
            handle=HANDLE,
        )
        quest_result = current_quest(
            database_connection,
            CATALOG,
            handle=HANDLE,
            assigned_at="2026-08-01T09:02:00Z",
            source=SOURCE,
        )

        assert objective_result.session_id == "S3"
        assert objective_result.objective == CATALOG.session("S3").objectives[1]
        assert objective_result.evidence_since == "2026-08-01T09:00:00Z"
        assert quest_result.quest is None
        assert (
            get_assignment(
                database_connection,
                HANDLE,
                CATALOG.course.id,
                "make-first-pipe",
            )
            is None
        )


def test_session_objective_evidence_starts_at_early_release(
    migrated_database_path: Path,
) -> None:
    """An early mentor release opens evidence before the scheduled session start."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll_without_session_placement(database_connection)
        release_course(
            database_connection,
            CATALOG,
            CourseReleaseInput(
                session_reached="S1",
                updated_at="2026-07-18T08:30:00Z",
                source=SOURCE,
            ),
        )

        assert (
            current_session_objective(
                database_connection,
                CATALOG,
                handle=HANDLE,
            ).evidence_since
            == "2026-07-18T08:30:00Z"
        )


def test_current_quest_prefers_lowest_sequence_assigned_incomplete(
    migrated_database_path: Path,
) -> None:
    """Assigned incomplete quests win over newly assignable quests."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        current_quest(
            database_connection,
            CATALOG,
            handle=HANDLE,
            assigned_at="2026-07-19T09:00:00Z",
            source=SOURCE,
        )
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle=HANDLE,
                course_id=CATALOG.course.id,
                quest_id=CATALOG.course.quests[1].id,
                assigned_at="2026-07-19T09:01:00Z",
                source=SOURCE,
            ),
        )

        assert (
            current_quest(
                database_connection,
                CATALOG,
                handle=HANDLE,
                assigned_at="2026-07-19T09:02:00Z",
                source=SOURCE,
            ).quest
            == CATALOG.course.quests[0]
        )


def test_current_quest_supersedes_higher_sequence_assignment(
    migrated_database_path: Path,
) -> None:
    """An older assignment cannot block a newly earlier current quest."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        for timestamp in (
            "2026-07-19T09:00:00Z",
            "2026-07-20T09:00:00Z",
            "2026-07-21T09:00:00Z",
        ):
            _complete_current_quest(database_connection, timestamp)
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle=HANDLE,
                course_id=CATALOG.course.id,
                quest_id="read-file-ends",
                assigned_at="2026-07-22T09:01:00Z",
                source=SOURCE,
            ),
        )

        result = current_quest(
            database_connection,
            CATALOG,
            handle=HANDLE,
            assigned_at="2026-07-22T09:02:00Z",
            source=SOURCE,
        )

        assert result.quest == CATALOG.quest("explain-ls")
        assert result.assignment == get_assignment(
            database_connection,
            HANDLE,
            CATALOG.course.id,
            "explain-ls",
        )
        assert result.assigned_now is True


def test_current_quest_ignores_future_session_assignment(
    migrated_database_path: Path,
) -> None:
    """Assignments outside the reached session range do not become current."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle=HANDLE,
                course_id=CATALOG.course.id,
                quest_id=_future_session_quest().id,
                assigned_at="2026-07-19T09:00:00Z",
                source=SOURCE,
            ),
        )

        assert (
            current_quest(
                database_connection,
                CATALOG,
                handle=HANDLE,
                assigned_at="2026-07-19T09:01:00Z",
                source=SOURCE,
            ).quest
            == CATALOG.course.quests[0]
        )


def test_current_quest_prioritizes_current_session_after_advancing(
    migrated_database_path: Path,
) -> None:
    """Current-session work outranks incomplete assignments from earlier sessions."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        current_quest(
            database_connection,
            CATALOG,
            handle=HANDLE,
            assigned_at="2026-07-19T09:00:00Z",
            source=SOURCE,
        )
        release_course(
            database_connection,
            CATALOG,
            CourseReleaseInput(
                session_reached="S2",
                updated_at="2026-07-25T09:00:00Z",
                source=SOURCE,
            ),
        )
        _write_completed_session_objectives(database_connection, "S2")

        result = current_quest(
            database_connection,
            CATALOG,
            handle=HANDLE,
            assigned_at="2026-07-25T09:01:00Z",
            source=SOURCE,
        )

        assert result.quest == CATALOG.quest("build-playground")
        assert (
            current_quest(
                database_connection,
                CATALOG,
                handle=HANDLE,
                assigned_at="2026-07-25T09:02:00Z",
                source=SOURCE,
            ).quest
            == result.quest
        )


def test_current_session_work_precedes_older_objectives_and_quests(
    migrated_database_path: Path,
) -> None:
    """Older backlog resumes only after every current-session task is complete."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection, objectives_complete=False)
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle=HANDLE,
                course_id=CATALOG.course.id,
                quest_id="prove-shell-alive",
                assigned_at="2026-07-19T09:00:00Z",
                source=SOURCE,
            ),
        )
        release_course(
            database_connection,
            CATALOG,
            CourseReleaseInput(
                session_reached="S2",
                updated_at="2026-07-25T09:00:00Z",
                source=SOURCE,
            ),
        )

        assert (
            current_session_objective(
                database_connection,
                CATALOG,
                handle=HANDLE,
            ).objective
            == CATALOG.session("S2").objectives[0]
        )

        _write_completed_session_objectives(database_connection, "S2")

        assert (
            current_session_objective(database_connection, CATALOG, handle=HANDLE).objective is None
        )
        assert current_quest(
            database_connection,
            CATALOG,
            handle=HANDLE,
            assigned_at="2026-07-25T09:01:00Z",
            source=SOURCE,
        ).quest == CATALOG.quest("build-playground")

        for quest in CATALOG.quests_available_after("S2"):
            write_quest_completion(
                database_connection,
                QuestCompletion(
                    handle=HANDLE,
                    course_id=CATALOG.course.id,
                    quest_id=quest.id,
                    attempt_id=None,
                    completed_at="2026-07-25T09:02:00Z",
                    source=SOURCE,
                ),
            )

        objective_result = current_session_objective(
            database_connection,
            CATALOG,
            handle=HANDLE,
        )
        assert objective_result.session_id == "S1"
        assert objective_result.objective == CATALOG.session("S1").objectives[0]


def test_completed_current_quest_is_skipped(migrated_database_path: Path) -> None:
    """Completing an assigned quest moves current quest selection forward."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        _complete_current_quest(database_connection, "2026-07-19T09:00:00Z")

        assert (
            current_quest(
                database_connection,
                CATALOG,
                handle=HANDLE,
                assigned_at="2026-07-20T09:00:00Z",
                source=SOURCE,
            ).quest
            == CATALOG.course.quests[1]
        )


def test_passed_completion_writes_progress_side_effects(migrated_database_path: Path) -> None:
    """Quest completion writes durable progress, audit, and projection work."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        result = _complete_current_quest(database_connection, "2026-07-19T09:00:00Z")

        assert result.completed_now is True
        assert result.score_total == CATALOG.course.quests[0].score + 5
        assert (
            get_quest_completion(
                database_connection,
                HANDLE,
                CATALOG.course.id,
                CATALOG.course.quests[0].id,
            )
            == result.completion
        )
        assert total_score_for_course(database_connection, HANDLE, CATALOG.course.id) == 30
        assert [
            (entry.amount, entry.reason, entry.related_id)
            for entry in list_score_entries(database_connection, HANDLE, CATALOG.course.id)
        ] == [
            (25, "quest_completed", CATALOG.course.quests[0].id),
            (5, "quest_completion_speed_bonus", CATALOG.course.quests[0].id),
        ]
        assert {
            event.event_type for event in list_unexported_audit_events(database_connection, 20)
        } >= {"quest_attempted", "quest_completed", "score_awarded"}
        assert {item.kind for item in list_pending_outbox_items(database_connection, 20)} == {
            "projection"
        }


def test_first_three_quest_completions_receive_speed_bonuses(
    migrated_database_path: Path,
) -> None:
    """The first three verified completions of a quest receive descending bonuses."""
    with connect_database(migrated_database_path) as database_connection:
        for handle, speed_bonus in (
            ("alice", 5),
            ("bob", 3),
            ("charlie", 2),
            ("dana", 0),
        ):
            _enroll(database_connection, handle=handle)
            result = _complete_current_quest(
                database_connection,
                "2026-07-19T09:00:00Z",
                handle=handle,
            )

            assert result.score_total == 25 + speed_bonus
            assert [
                entry.amount
                for entry in list_score_entries(
                    database_connection,
                    handle,
                    CATALOG.course.id,
                )
            ] == [25, *([speed_bonus] if speed_bonus else [])]


def test_non_students_do_not_receive_or_consume_speed_bonuses(
    migrated_database_path: Path,
) -> None:
    """Unranked participants receive ordinary scores without affecting student bonuses."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection, handle="mentor", rank_eligible=False)
        non_student_result = _complete_current_quest(
            database_connection,
            "2026-07-19T09:00:00Z",
            handle="mentor",
        )
        _enroll(database_connection, handle="alice")
        student_result = _complete_current_quest(
            database_connection,
            "2026-07-19T09:01:00Z",
            handle="alice",
        )

    assert non_student_result.score_total == 25
    assert student_result.score_total == 30


def test_session_objective_completions_award_base_and_speed_scores(
    migrated_database_path: Path,
) -> None:
    """Session objectives use the quest completion speed bonus schedule."""
    objective_id = CATALOG.session("S1").objectives[0].id
    with connect_database(migrated_database_path) as database_connection:
        for handle, speed_bonus in (
            ("alice", 5),
            ("bob", 3),
            ("charlie", 2),
            ("dana", 0),
        ):
            _enroll(database_connection, handle=handle, objectives_complete=False)
            complete_session_objective(
                database_connection,
                CATALOG,
                handle=handle,
                session_id="S1",
                objective_id=objective_id,
                completed_at="2026-07-19T09:00:00Z",
                evidence={"passed": True},
            )

            assert total_score_for_course(database_connection, handle, CATALOG.course.id) == (
                50 + speed_bonus
            )

        complete_session_objective(
            database_connection,
            CATALOG,
            handle="alice",
            session_id="S1",
            objective_id=objective_id,
            completed_at="2026-07-19T09:01:00Z",
            evidence={"passed": True},
        )

        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 55


@pytest.mark.parametrize(
    ("objectives_complete", "session_id", "objective_id"),
    [
        (False, "S1", "prove-shell-alive"),
        (True, "S2", "ssh-public-key"),
    ],
    ids=("out-of-order", "unreleased"),
)
def test_session_objective_completion_requires_current_released_objective(
    migrated_database_path: Path,
    objectives_complete: bool,
    session_id: str,
    objective_id: str,
) -> None:
    """The objective write boundary rejects skipped and unreleased work."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection, objectives_complete=objectives_complete)

        with pytest.raises(ProgressServiceError, match="session objective is not current"):
            complete_session_objective(
                database_connection,
                CATALOG,
                handle=HANDLE,
                session_id=session_id,
                objective_id=objective_id,
                completed_at="2026-07-19T09:00:00Z",
                evidence={"passed": True},
                source=SOURCE,
            )

        assert objective_id not in list_completed_objective_ids(
            database_connection,
            HANDLE,
            CATALOG.course.id,
            session_id,
        )
        assert total_score_for_course(database_connection, HANDLE, CATALOG.course.id) == 0


def test_session_objective_promotion_is_recorded_and_audited(
    migrated_database_path: Path,
) -> None:
    """An objective score award records a newly crossed tier exactly once."""
    objective_id = CATALOG.session("S1").objectives[0].id
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection, objectives_complete=False)
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle=HANDLE,
                course_id=CATALOG.course.id,
                amount=445,
                reason="test",
                related_type="test",
                related_id="before-objective",
                created_at="2026-07-19T08:00:00Z",
            ),
        )

        result = complete_session_objective(
            database_connection,
            CATALOG,
            handle=HANDLE,
            session_id="S1",
            objective_id=objective_id,
            completed_at="2026-07-19T09:00:00Z",
            evidence={"passed": True},
            source=SOURCE,
        )

        assert [promotion.tier_id for promotion in result.tier_promotions] == ["apprentice"]
        assert [
            promotion.tier_id
            for promotion in list_tier_promotions(database_connection, HANDLE, CATALOG.course.id)
        ] == ["apprentice"]
        assert [
            event.payload
            for event in list_unexported_audit_events(database_connection, 10)
            if event.event_type == "tier_promoted"
        ] == [{"course_id": CATALOG.course.id, "tier_id": "apprentice", "score_total": 500}]


def test_failed_attempt_records_evidence_without_completion(migrated_database_path: Path) -> None:
    """Failed validation attempts are durable but do not award progress."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        quest = _assign_current_quest(database_connection, "2026-07-19T09:00:00Z")
        result = record_attempt(
            database_connection,
            CATALOG,
            QuestAttemptInput(
                handle=HANDLE,
                quest_id=quest.id,
                attempted_at="2026-07-19T09:00:00Z",
                source=SOURCE,
                outcome="failed",
                failure_reason="incomplete-evidence",
                evidence={"passed": False},
            ),
        )

        assert result.attempt.outcome == "failed"
        assert (
            get_quest_completion(database_connection, HANDLE, CATALOG.course.id, quest.id) is None
        )
        assert total_score_for_course(database_connection, HANDLE, CATALOG.course.id) == 0
        assert list_unexported_audit_events(database_connection, 10)[-1].payload == {
            "attempt_id": result.attempt.id,
            "course_id": CATALOG.course.id,
            "failure_reason": "incomplete-evidence",
            "outcome": "failed",
            "quest_id": quest.id,
        }


def test_operational_validation_failure_writes_safe_audit_metadata(
    migrated_database_path: Path,
) -> None:
    """Operational validation failures are logged without duplicating evidence."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        quest = _assign_current_quest(database_connection, "2026-07-19T09:00:00Z")
        result = record_attempt(
            database_connection,
            CATALOG,
            QuestAttemptInput(
                handle=HANDLE,
                quest_id=quest.id,
                attempted_at="2026-07-19T09:00:00Z",
                source=SOURCE,
                outcome="failed",
                failure_reason="permission-denied",
                evidence={
                    "catalog_path": "~/private.txt",
                    "failure_reason": "permission-denied",
                    "path_category": "learner-home",
                },
            ),
        )

        operational_event = list_unexported_audit_events(database_connection, 10)[-1]
        assert operational_event.event_type == "operational_validation_failed"
        assert operational_event.payload == {
            "attempt_id": result.attempt.id,
            "course_id": CATALOG.course.id,
            "failure_reason": "permission-denied",
            "quest_id": quest.id,
        }


def test_completion_rejects_failed_attempt(migrated_database_path: Path) -> None:
    """The service accepts only matching passed attempts for completion."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        quest = _assign_current_quest(database_connection, "2026-07-19T09:00:00Z")
        attempt_id = _record_attempt(
            database_connection,
            quest.id,
            "failed",
            "2026-07-19T09:00:00Z",
        )

        with pytest.raises(RepositoryError, match="quest completion attempt did not pass"):
            complete_quest(
                database_connection,
                CATALOG,
                QuestCompletionInput(
                    handle=HANDLE,
                    quest_id=quest.id,
                    attempt_id=attempt_id,
                    completed_at="2026-07-19T09:01:00Z",
                    source=SOURCE,
                ),
            )

        assert (
            get_quest_completion(database_connection, HANDLE, CATALOG.course.id, quest.id) is None
        )
        assert total_score_for_course(database_connection, HANDLE, CATALOG.course.id) == 0


def test_four_daily_completions_promote_apprentice(
    migrated_database_path: Path,
) -> None:
    """Tier promotions are recorded on first-time score threshold crossings."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle=HANDLE,
                course_id=CATALOG.course.id,
                amount=380,
                reason="test",
                related_type="test",
                related_id="before-completions",
                created_at="2026-07-18T09:00:00Z",
            ),
        )
        for quest_number in range(4):
            _complete_current_quest(
                database_connection,
                f"2026-07-{19 + quest_number:02d}T09:00:00Z",
            )

        assert total_score_for_course(database_connection, HANDLE, CATALOG.course.id) == 500
        assert [
            promotion.tier_id
            for promotion in list_tier_promotions(database_connection, HANDLE, CATALOG.course.id)
        ] == ["apprentice"]
        assert {
            event.event_type for event in list_unexported_audit_events(database_connection, 50)
        } >= {"tier_promoted"}


def test_repeating_completion_does_not_duplicate_score(migrated_database_path: Path) -> None:
    """Retrying a completed quest returns existing completion without double-awarding score."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        first_completion = _complete_current_quest(database_connection, "2026-07-19T09:00:00Z")
        if first_completion.completion.attempt_id is None:
            raise AssertionError("expected completion attempt id")
        retry_completion = complete_quest(
            database_connection,
            CATALOG,
            QuestCompletionInput(
                handle=HANDLE,
                quest_id=CATALOG.course.quests[0].id,
                attempt_id=first_completion.completion.attempt_id,
                completed_at="2026-07-19T09:03:00Z",
                source=SOURCE,
            ),
        )

        assert retry_completion.completed_now is False
        assert retry_completion.completion == first_completion.completion
        assert total_score_for_course(database_connection, HANDLE, CATALOG.course.id) == 30
        assert len(list_score_entries(database_connection, HANDLE, CATALOG.course.id)) == 2
        assert len(list_quest_completions(database_connection, HANDLE, CATALOG.course.id)) == 1


def test_completion_side_effects_roll_back_together(migrated_database_path: Path) -> None:
    """A failure after completion insert rolls back all service-owned side effects."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        quest = _assign_current_quest(database_connection, "2026-07-19T09:00:00Z")
        attempt_id = _record_attempt(
            database_connection,
            quest.id,
            "passed",
            "2026-07-19T09:00:00Z",
        )
        _write_conflicting_score(database_connection, quest.id)
        pending_outbox_count = len(list_pending_outbox_items(database_connection, 20))

        with pytest.raises(RepositoryError, match="conflicting score ledger entry"):
            complete_quest(
                database_connection,
                CATALOG,
                QuestCompletionInput(
                    handle=HANDLE,
                    quest_id=quest.id,
                    attempt_id=attempt_id,
                    completed_at="2026-07-19T09:01:00Z",
                    source=SOURCE,
                ),
            )

        assert (
            get_quest_completion(database_connection, HANDLE, CATALOG.course.id, quest.id) is None
        )
        assert total_score_for_course(database_connection, HANDLE, CATALOG.course.id) == 1
        assert len(list_pending_outbox_items(database_connection, 20)) == pending_outbox_count


def test_attempt_rejects_unassigned_quest(migrated_database_path: Path) -> None:
    """Direct attempts cannot bypass quest assignment."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)

        with pytest.raises(ProgressServiceError, match="quest is not assigned"):
            record_attempt(
                database_connection,
                CATALOG,
                QuestAttemptInput(
                    handle=HANDLE,
                    quest_id=CATALOG.course.quests[0].id,
                    attempted_at="2026-07-19T09:00:00Z",
                    source=SOURCE,
                    outcome="passed",
                    evidence={"passed": True},
                ),
            )


def test_quest_mutations_reject_preexisting_assignment_while_objectives_remain(
    migrated_database_path: Path,
) -> None:
    """A stale assignment cannot bypass objective gating at either write boundary."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection, objectives_complete=False)
        quest = CATALOG.course.quests[0]
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle=HANDLE,
                course_id=CATALOG.course.id,
                quest_id=quest.id,
                assigned_at="2026-07-18T09:00:00Z",
                source=SOURCE,
            ),
        )

        with pytest.raises(ProgressServiceError, match="objectives are incomplete"):
            record_attempt(
                database_connection,
                CATALOG,
                QuestAttemptInput(
                    handle=HANDLE,
                    quest_id=quest.id,
                    attempted_at="2026-07-18T09:01:00Z",
                    source=SOURCE,
                    outcome="passed",
                    evidence={"passed": True},
                ),
            )

        assert database_connection.execute(
            "select count(*) from quest_attempts",
        ).fetchone() == (0,)
        with pytest.raises(ProgressServiceError, match="objectives are incomplete"):
            complete_quest(
                database_connection,
                CATALOG,
                QuestCompletionInput(
                    handle=HANDLE,
                    quest_id=quest.id,
                    attempt_id=_record_repository_attempt(
                        database_connection,
                        quest.id,
                        "passed",
                        "2026-07-18T09:01:00Z",
                    ),
                    completed_at="2026-07-18T09:02:00Z",
                    source=SOURCE,
                ),
            )

        assert (
            get_quest_completion(
                database_connection,
                HANDLE,
                CATALOG.course.id,
                quest.id,
            )
            is None
        )
        assert total_score_for_course(database_connection, HANDLE, CATALOG.course.id) == 0


def test_attempt_rejects_assigned_quest_blocked_by_lower_sequence(
    migrated_database_path: Path,
) -> None:
    """Direct attempts cannot skip an earlier assigned incomplete quest."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        _assign_current_quest(database_connection, "2026-07-19T09:00:00Z")
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle=HANDLE,
                course_id=CATALOG.course.id,
                quest_id=CATALOG.course.quests[1].id,
                assigned_at="2026-07-19T09:01:00Z",
                source=SOURCE,
            ),
        )

        with pytest.raises(ProgressServiceError, match="quest is not currently available"):
            record_attempt(
                database_connection,
                CATALOG,
                QuestAttemptInput(
                    handle=HANDLE,
                    quest_id=CATALOG.course.quests[1].id,
                    attempted_at="2026-07-19T09:02:00Z",
                    source=SOURCE,
                    outcome="passed",
                    evidence={"passed": True},
                ),
            )


def test_attempt_rejects_assigned_quest_blocked_by_lower_unassigned_quest(
    migrated_database_path: Path,
) -> None:
    """Direct attempts cannot bypass a lower-sequence unassigned quest."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        for timestamp in (
            "2026-07-19T09:00:00Z",
            "2026-07-20T09:00:00Z",
            "2026-07-21T09:00:00Z",
            "2026-07-22T09:00:00Z",
        ):
            _complete_current_quest(database_connection, timestamp)
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle=HANDLE,
                course_id=CATALOG.course.id,
                quest_id="build-playground",
                assigned_at="2026-07-22T09:01:00Z",
                source=SOURCE,
            ),
        )

        with pytest.raises(ProgressServiceError, match="quest is not currently available"):
            record_attempt(
                database_connection,
                CATALOG,
                QuestAttemptInput(
                    handle=HANDLE,
                    quest_id="build-playground",
                    attempted_at="2026-07-22T09:02:00Z",
                    source=SOURCE,
                    outcome="passed",
                    evidence={"passed": True},
                ),
            )


def test_attempt_rejects_future_session_assignment(migrated_database_path: Path) -> None:
    """Direct attempts cannot use assignments outside the reached session range."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        future_quest = _future_session_quest()
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle=HANDLE,
                course_id=CATALOG.course.id,
                quest_id=future_quest.id,
                assigned_at="2026-07-19T09:00:00Z",
                source=SOURCE,
            ),
        )

        with pytest.raises(ProgressServiceError, match="quest is not currently available"):
            record_attempt(
                database_connection,
                CATALOG,
                QuestAttemptInput(
                    handle=HANDLE,
                    quest_id=future_quest.id,
                    attempted_at="2026-07-19T09:01:00Z",
                    source=SOURCE,
                    outcome="passed",
                    evidence={"passed": True},
                ),
            )


def test_completion_rejects_unassigned_quest(migrated_database_path: Path) -> None:
    """Direct completion cannot bypass quest assignment."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        quest = CATALOG.course.quests[0]

        with pytest.raises(ProgressServiceError, match="quest is not assigned"):
            complete_quest(
                database_connection,
                CATALOG,
                QuestCompletionInput(
                    handle=HANDLE,
                    quest_id=quest.id,
                    attempt_id=_record_repository_attempt(
                        database_connection,
                        quest.id,
                        "passed",
                        "2026-07-19T09:00:00Z",
                    ),
                    completed_at="2026-07-19T09:01:00Z",
                    source=SOURCE,
                ),
            )


def test_completion_rejects_assigned_quest_blocked_by_lower_sequence(
    migrated_database_path: Path,
) -> None:
    """Direct completion cannot skip an earlier assigned incomplete quest."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        _assign_current_quest(database_connection, "2026-07-19T09:00:00Z")
        blocked_quest = CATALOG.course.quests[1]
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle=HANDLE,
                course_id=CATALOG.course.id,
                quest_id=blocked_quest.id,
                assigned_at="2026-07-19T09:01:00Z",
                source=SOURCE,
            ),
        )

        with pytest.raises(ProgressServiceError, match="quest is not currently available"):
            complete_quest(
                database_connection,
                CATALOG,
                QuestCompletionInput(
                    handle=HANDLE,
                    quest_id=blocked_quest.id,
                    attempt_id=_record_repository_attempt(
                        database_connection,
                        blocked_quest.id,
                        "passed",
                        "2026-07-19T09:02:00Z",
                    ),
                    completed_at="2026-07-19T09:03:00Z",
                    source=SOURCE,
                ),
            )


def test_completion_rejects_future_session_assignment(migrated_database_path: Path) -> None:
    """Direct completion cannot use assignments outside the reached session range."""
    with connect_database(migrated_database_path) as database_connection:
        _enroll(database_connection)
        future_quest = _future_session_quest()
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle=HANDLE,
                course_id=CATALOG.course.id,
                quest_id=future_quest.id,
                assigned_at="2026-07-19T09:00:00Z",
                source=SOURCE,
            ),
        )

        with pytest.raises(ProgressServiceError, match="quest is not currently available"):
            complete_quest(
                database_connection,
                CATALOG,
                QuestCompletionInput(
                    handle=HANDLE,
                    quest_id=future_quest.id,
                    attempt_id=_record_repository_attempt(
                        database_connection,
                        future_quest.id,
                        "passed",
                        "2026-07-19T09:01:00Z",
                    ),
                    completed_at="2026-07-19T09:02:00Z",
                    source=SOURCE,
                ),
            )


def test_schema_has_no_mutable_current_quest_column(migrated_database_path: Path) -> None:
    """Current quest is selected deterministically, not stored as a mutable column."""
    with connect_database(migrated_database_path) as database_connection:
        column_records = cast(
            "list[tuple[int, str, str, int, object, int]]",
            database_connection.execute("pragma table_info(cohort_memberships)").fetchall(),
        )

    assert "current_quest" not in {column_record[1] for column_record in column_records}


def _enroll(
    database_connection: sqlite3.Connection,
    *,
    handle: str = HANDLE,
    rank_eligible: bool = True,
    objectives_complete: bool = True,
) -> None:
    _enroll_without_session_placement(
        database_connection,
        handle=handle,
        rank_eligible=rank_eligible,
    )
    release_course(
        database_connection,
        CATALOG,
        CourseReleaseInput(
            session_reached="S1",
            updated_at=JOINED_AT,
            source=SOURCE,
        ),
    )
    if objectives_complete:
        _write_completed_session_objectives(database_connection, "S1", handle=handle)


def _enroll_without_session_placement(
    database_connection: sqlite3.Connection,
    *,
    handle: str = HANDLE,
    rank_eligible: bool = True,
) -> None:
    ensure_learner(
        database_connection,
        EnsureLearnerInput(handle=handle, joined_at=JOINED_AT, source=SOURCE),
    )
    enroll(
        database_connection,
        EnrollmentInput(
            handle=handle,
            course_id=CATALOG.course.id,
            joined_at=JOINED_AT,
            source=SOURCE,
            rank_eligible=rank_eligible,
        ),
    )


def _complete_current_quest(
    database_connection: sqlite3.Connection,
    timestamp: str,
    *,
    handle: str = HANDLE,
) -> QuestCompletionResult:
    quest = _assign_current_quest(database_connection, timestamp, handle=handle)
    return complete_quest(
        database_connection,
        CATALOG,
        QuestCompletionInput(
            handle=handle,
            quest_id=quest.id,
            attempt_id=_record_attempt(
                database_connection,
                quest.id,
                "passed",
                timestamp,
                handle=handle,
            ),
            completed_at=timestamp,
            source=SOURCE,
        ),
    )


def _record_attempt(
    database_connection: sqlite3.Connection,
    quest_id: str,
    outcome: QuestAttemptOutcome,
    timestamp: str,
    *,
    handle: str = HANDLE,
) -> int:
    result = record_attempt(
        database_connection,
        CATALOG,
        QuestAttemptInput(
            handle=handle,
            quest_id=quest_id,
            attempted_at=timestamp,
            source=SOURCE,
            outcome=outcome,
            failure_reason=None if outcome == "passed" else "incomplete-evidence",
            evidence={"passed": outcome == "passed"},
        ),
    )
    if result.attempt.id is None:
        raise AssertionError("expected attempt id")
    return result.attempt.id


def _record_repository_attempt(
    database_connection: sqlite3.Connection,
    quest_id: str,
    outcome: QuestAttemptOutcome,
    timestamp: str,
) -> int:
    return record_quest_attempt(
        database_connection,
        QuestAttempt(
            id=None,
            handle=HANDLE,
            course_id=CATALOG.course.id,
            quest_id=quest_id,
            attempted_at=timestamp,
            source=SOURCE,
            outcome=outcome,
            failure_reason=None if outcome == "passed" else "incomplete-evidence",
            evidence={"passed": outcome == "passed"},
        ),
    )


def _assign_current_quest(
    database_connection: sqlite3.Connection,
    timestamp: str,
    *,
    handle: str = HANDLE,
) -> Quest:
    quest = current_quest(
        database_connection,
        CATALOG,
        handle=handle,
        assigned_at=timestamp,
        source=SOURCE,
    ).quest
    if quest is None:
        raise AssertionError("expected a current quest")
    return quest


def _future_session_quest() -> Quest:
    return next(quest for quest in CATALOG.course.quests if quest.available_after_session == "S2")


def _write_completed_session_objectives(
    database_connection: sqlite3.Connection,
    session_id: str,
    *,
    handle: str = HANDLE,
) -> None:
    for objective in CATALOG.session(session_id).objectives:
        write_session_objective_completion(
            database_connection,
            SessionObjectiveCompletion(
                handle=handle,
                course_id=CATALOG.course.id,
                session_id=session_id,
                objective_id=objective.id,
                completed_at="2026-07-19T08:00:00Z",
                evidence_json="{}",
            ),
        )


def _write_conflicting_score(database_connection: sqlite3.Connection, quest_id: str) -> None:
    with database_connection:
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle=HANDLE,
                course_id=CATALOG.course.id,
                amount=1,
                reason="quest_completed",
                related_type="quest",
                related_id=quest_id,
                created_at="2026-07-19T08:59:00Z",
            ),
        )
