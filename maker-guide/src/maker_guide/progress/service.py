"""Transactional progress service flows."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from maker_guide.curriculum.models import CourseCatalog, Quest
from maker_guide.curriculum.tiers import crossed_tiers
from maker_guide.progress.models import (
    CourseReleaseInput,
    CourseReleaseResult,
    CurrentQuestResult,
    CurrentSessionObjectiveResult,
    ProgressServiceError,
    QuestAttemptInput,
    QuestAttemptResult,
    QuestCompletionInput,
    QuestCompletionResult,
    SessionObjectiveCompletionResult,
)
from maker_guide.progress.validation import QuestValidationResult
from maker_guide.repositories.audit_event import AuditEvent, append_audit_event
from maker_guide.repositories.cohort_membership import (
    CohortMembership,
    get_membership,
    list_memberships,
)
from maker_guide.repositories.course_release import (
    CourseRelease,
    get_course_release,
    get_course_session_released_at,
    upsert_course_release,
)
from maker_guide.repositories.helpers import JsonPayload, RepositoryError, dump_json, transaction
from maker_guide.repositories.outbox_item import (
    ProjectionOutboxReason,
    enqueue_outbox_item,
    projection_outbox_item,
)
from maker_guide.repositories.quest_assignment import (
    QuestAssignment,
    assign_quest,
    get_assignment,
    list_assignments,
)
from maker_guide.repositories.quest_attempt import (
    QuestAttempt,
    get_quest_attempt,
    record_quest_attempt,
)
from maker_guide.repositories.quest_completion import (
    QuestCompletion,
    count_rank_eligible_quest_completions,
    get_quest_completion,
    list_completed_quest_ids,
)
from maker_guide.repositories.quest_completion import (
    complete_quest as complete_quest_repository,
)
from maker_guide.repositories.score_ledger import (
    ScoreLedgerEntry,
    add_score_entry,
    total_score_for_course,
)
from maker_guide.repositories.session_objective_completion import (
    SessionObjectiveCompletion,
    count_rank_eligible_session_objective_completions,
    list_completed_objective_ids,
)
from maker_guide.repositories.session_objective_completion import (
    complete_session_objective as complete_session_objective_repository,
)
from maker_guide.repositories.tier_promotion import (
    TierPromotion,
    list_tier_promotions,
    record_tier_promotion,
)

_OPERATIONAL_VALIDATION_FAILURE_REASONS = frozenset(
    {
        "unsupported-validation",
        "unknown-user",
        "unsafe-path",
        "path-escapes-scope",
        "broken-symlink",
        "symlink-loop",
        "permission-denied",
        "read-error",
        "not-regular-file",
        "file-too-large",
        "file-decode-error",
        "invalid-regex",
        "unsupported-port-formula",
    },
)
_SPEED_BONUSES = (5, 3, 2)
_SESSION_OBJECTIVE_SCORE = 50


@dataclass(frozen=True, kw_only=True, slots=True)
class _CompletedQuestEffects:
    """Side effects derived from a newly completed quest."""

    quest: Quest
    """Completed quest definition."""

    score_total: int
    """Course score total after the completion."""

    score_awarded: int
    """Score awarded for the completion, including a speed bonus when applicable."""

    tier_promotions: tuple[TierPromotion, ...]
    """Tier promotions recorded by the completion."""


def release_course(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    release_input: CourseReleaseInput,
) -> CourseReleaseResult:
    """Release a session to every learner enrolled in a course."""
    with transaction(database_connection):
        catalog.session(release_input.session_reached)
        existing_release = get_course_release(database_connection, catalog.course.id)
        if (
            existing_release is not None
            and existing_release.session_reached == release_input.session_reached
        ):
            return CourseReleaseResult(course_release=existing_release, changed=False)
        next_session_index = (
            0
            if existing_release is None
            else len(catalog.sessions_through(existing_release.session_reached))
        )
        if (
            next_session_index >= len(catalog.course.sessions)
            or catalog.course.sessions[next_session_index].id != release_input.session_reached
        ):
            raise ProgressServiceError("course sessions must be released one at a time")

        course_release = CourseRelease(
            course_id=catalog.course.id,
            session_reached=release_input.session_reached,
            released_at=release_input.updated_at,
        )
        upsert_course_release(
            database_connection,
            course_release,
        )
        append_audit_event(
            database_connection,
            AuditEvent(
                event_type="course_released",
                handle=None,
                source=release_input.source,
                created_at=release_input.updated_at,
                payload={
                    "course_id": catalog.course.id,
                    "previous_session_reached": (
                        None if existing_release is None else existing_release.session_reached
                    ),
                    "session_reached": release_input.session_reached,
                },
            ),
        )
        for membership in list_memberships(database_connection, catalog.course.id):
            _enqueue_projection(
                database_connection,
                membership.handle,
                catalog.course.id,
                release_input.updated_at,
                "course_released",
            )
        return CourseReleaseResult(course_release=course_release, changed=True)


def current_quest(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    *,
    handle: str,
    assigned_at: str,
    source: str,
) -> CurrentQuestResult:
    """Return and persist the learner's deterministic current quest."""
    with transaction(database_connection):
        _require_membership(database_connection, handle, catalog.course.id)
        course_release = _require_course_release(database_connection, catalog.course.id)
        if course_release is None:
            raise ProgressServiceError("learner has not reached a course session")
        if (
            current_session_objective(
                database_connection,
                catalog,
                handle=handle,
            ).objective
            is not None
        ):
            return CurrentQuestResult(quest=None, assignment=None, assigned_now=False)

        completed_quest_ids = list_completed_quest_ids(
            database_connection,
            handle,
            catalog.course.id,
        )
        assigned_quest = _current_assigned_incomplete_quest(
            catalog,
            course_release.session_reached,
            _assignments_available_after_session(
                catalog,
                list_assignments(database_connection, handle, catalog.course.id),
                course_release.session_reached,
            ),
            completed_quest_ids,
        )
        next_quest = catalog.next_assignable_quest(
            course_release.session_reached,
            completed_quest_ids,
        )
        selected_quest = _current_quest(
            catalog,
            course_release.session_reached,
            assigned_quest,
            next_quest,
        )
        if selected_quest is None:
            return CurrentQuestResult(quest=None, assignment=None, assigned_now=False)
        if assigned_quest is not None and selected_quest.id == assigned_quest.id:
            return CurrentQuestResult(
                quest=assigned_quest,
                assignment=_require_assignment(
                    database_connection,
                    handle,
                    catalog.course.id,
                    assigned_quest.id,
                ),
                assigned_now=False,
            )

        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle=handle,
                course_id=catalog.course.id,
                quest_id=selected_quest.id,
                assigned_at=assigned_at,
                source=source,
            ),
        )
        append_audit_event(
            database_connection,
            AuditEvent(
                event_type="quest_assigned",
                handle=handle,
                source=source,
                created_at=assigned_at,
                payload={"course_id": catalog.course.id, "quest_id": selected_quest.id},
            ),
        )
        _enqueue_projection(
            database_connection,
            handle,
            catalog.course.id,
            assigned_at,
            "quest_assigned",
        )
        return CurrentQuestResult(
            quest=selected_quest,
            assignment=_require_assignment(
                database_connection,
                handle,
                catalog.course.id,
                selected_quest.id,
            ),
            assigned_now=True,
        )


def current_session_objective(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    *,
    handle: str,
) -> CurrentSessionObjectiveResult:
    """Return the current-session objective, then older backlog after current quests."""
    _require_membership(database_connection, handle, catalog.course.id)
    course_release = _require_course_release(database_connection, catalog.course.id)
    if course_release is None:
        raise ProgressServiceError("learner has not reached a course session")
    released_sessions = catalog.sessions_through(course_release.session_reached)
    current_session = released_sessions[-1]
    completed_quest_ids = list_completed_quest_ids(
        database_connection,
        handle,
        catalog.course.id,
    )
    for session in (current_session, *released_sessions[:-1]):
        completed_objective_ids = list_completed_objective_ids(
            database_connection,
            handle,
            catalog.course.id,
            session.id,
        )
        objective = next(
            (
                session_objective
                for session_objective in session.objectives
                if session_objective.id not in completed_objective_ids
            ),
            None,
        )
        if objective is not None:
            return CurrentSessionObjectiveResult(
                session_id=session.id,
                objective=objective,
                evidence_since=_session_evidence_since(
                    database_connection,
                    catalog,
                    course_release,
                    session.id,
                ),
            )
        if session == current_session and any(
            quest.id not in completed_quest_ids
            for quest in catalog.quests_available_after(current_session.id)
        ):
            break

    return CurrentSessionObjectiveResult(
        session_id=course_release.session_reached,
        objective=None,
        evidence_since=_session_evidence_since(
            database_connection,
            catalog,
            course_release,
            course_release.session_reached,
        ),
    )


def _session_evidence_since(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    course_release: CourseRelease,
    session_id: str,
) -> str:
    return min(
        get_course_session_released_at(
            database_connection,
            catalog.course.id,
            session_id,
        )
        or course_release.released_at,
        catalog.session(session_id).starts_at.isoformat().replace("+00:00", "Z"),
    )


def complete_session_objective(  # noqa: PLR0913
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    *,
    handle: str,
    session_id: str,
    objective_id: str,
    completed_at: str,
    evidence: JsonPayload,
    source: str = "system",
) -> SessionObjectiveCompletionResult:
    """Persist validated objective evidence without a manual signoff path."""
    with transaction(database_connection):
        membership = _require_membership(database_connection, handle, catalog.course.id)
        if objective_id not in {
            objective.id for objective in catalog.session(session_id).objectives
        }:
            raise ProgressServiceError("unknown session objective")
        if objective_id in list_completed_objective_ids(
            database_connection,
            handle,
            catalog.course.id,
            session_id,
        ):
            return SessionObjectiveCompletionResult(
                score_total=total_score_for_course(database_connection, handle, catalog.course.id),
                tier_promotions=(),
            )
        current_objective_result = current_session_objective(
            database_connection,
            catalog,
            handle=handle,
        )
        if (
            current_objective_result.session_id != session_id
            or current_objective_result.objective is None
            or current_objective_result.objective.id != objective_id
        ):
            raise ProgressServiceError("session objective is not current")
        previous_score_total = total_score_for_course(
            database_connection,
            handle,
            catalog.course.id,
        )
        complete_session_objective_repository(
            database_connection,
            SessionObjectiveCompletion(
                handle=handle,
                course_id=catalog.course.id,
                session_id=session_id,
                objective_id=objective_id,
                completed_at=completed_at,
                evidence_json=dump_json(evidence),
            ),
        )
        related_id = _session_objective_related_id(session_id, objective_id)
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle=handle,
                course_id=catalog.course.id,
                amount=_SESSION_OBJECTIVE_SCORE,
                reason="session_objective_completed",
                related_type="session_objective",
                related_id=related_id,
                created_at=completed_at,
            ),
        )
        speed_bonus = (
            _speed_bonus(
                count_rank_eligible_session_objective_completions(
                    database_connection,
                    catalog.course.id,
                    session_id,
                    objective_id,
                ),
            )
            if membership.rank_eligible
            else 0
        )
        if speed_bonus:
            add_score_entry(
                database_connection,
                ScoreLedgerEntry(
                    id=None,
                    handle=handle,
                    course_id=catalog.course.id,
                    amount=speed_bonus,
                    reason="session_objective_speed_bonus",
                    related_type="session_objective",
                    related_id=related_id,
                    created_at=completed_at,
                ),
            )
        score_total = total_score_for_course(database_connection, handle, catalog.course.id)
        tier_promotions = record_tier_promotions(
            database_connection,
            catalog,
            handle,
            completed_at,
            source,
            previous_score_total,
            score_total,
        )
        _enqueue_projection(
            database_connection,
            handle,
            catalog.course.id,
            completed_at,
            "session_objective_completed",
        )
        return SessionObjectiveCompletionResult(
            score_total=score_total,
            tier_promotions=tier_promotions,
        )


def record_session_objective_validation_failure(  # noqa: PLR0913
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    *,
    handle: str,
    session_id: str,
    objective_id: str,
    failed_at: str,
    source: str,
    validation_result: QuestValidationResult,
) -> None:
    """Audit a failed check without adding an objective-attempt subsystem."""
    if validation_result.passed or validation_result.failure_reason is None:
        raise ProgressServiceError("session objective validation failure is invalid")
    with transaction(database_connection):
        current_objective_result = current_session_objective(
            database_connection,
            catalog,
            handle=handle,
        )
        if (
            current_objective_result.session_id != session_id
            or current_objective_result.objective is None
            or current_objective_result.objective.id != objective_id
        ):
            raise ProgressServiceError("session objective is not current")
        append_audit_event(
            database_connection,
            AuditEvent(
                event_type="session_objective_validation_failed",
                handle=handle,
                source=source,
                created_at=failed_at,
                payload={
                    "course_id": catalog.course.id,
                    "session_id": session_id,
                    "objective_id": objective_id,
                    "failure_reason": validation_result.failure_reason,
                    "evidence": validation_result.evidence,
                },
            ),
        )
        _append_operational_validation_audit_event(
            database_connection,
            catalog,
            handle=handle,
            source=source,
            failed_at=failed_at,
            failure_reason=validation_result.failure_reason,
            context={"session_id": session_id, "objective_id": objective_id},
        )


def record_attempt(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    attempt_input: QuestAttemptInput,
) -> QuestAttemptResult:
    """Record one deterministic quest validation attempt."""
    with transaction(database_connection):
        membership = _require_membership(
            database_connection,
            attempt_input.handle,
            catalog.course.id,
        )
        catalog.quest(attempt_input.quest_id)
        _require_current_assignment(
            database_connection,
            catalog,
            membership,
            attempt_input.quest_id,
        )
        attempt_id = record_quest_attempt(
            database_connection,
            QuestAttempt(
                id=None,
                handle=attempt_input.handle,
                course_id=catalog.course.id,
                quest_id=attempt_input.quest_id,
                attempted_at=attempt_input.attempted_at,
                source=attempt_input.source,
                outcome=attempt_input.outcome,
                failure_reason=attempt_input.failure_reason,
                evidence=attempt_input.evidence,
            ),
        )
        append_audit_event(
            database_connection,
            AuditEvent(
                event_type="quest_attempted",
                handle=attempt_input.handle,
                source=attempt_input.source,
                created_at=attempt_input.attempted_at,
                payload={
                    "course_id": catalog.course.id,
                    "quest_id": attempt_input.quest_id,
                    "attempt_id": attempt_id,
                    "outcome": attempt_input.outcome,
                    "failure_reason": attempt_input.failure_reason,
                },
            ),
        )
        _append_operational_validation_audit_event(
            database_connection,
            catalog,
            handle=attempt_input.handle,
            source=attempt_input.source,
            failed_at=attempt_input.attempted_at,
            failure_reason=attempt_input.failure_reason,
            context={"attempt_id": attempt_id, "quest_id": attempt_input.quest_id},
        )
        return QuestAttemptResult(attempt=_require_attempt(database_connection, attempt_id))


def _append_operational_validation_audit_event(  # noqa: PLR0913 - Audit context is explicit.
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    *,
    handle: str,
    source: str,
    failed_at: str,
    failure_reason: str | None,
    context: JsonPayload,
) -> None:
    if failure_reason not in _OPERATIONAL_VALIDATION_FAILURE_REASONS:
        return
    append_audit_event(
        database_connection,
        AuditEvent(
            event_type="operational_validation_failed",
            handle=handle,
            source=source,
            created_at=failed_at,
            payload={
                "course_id": catalog.course.id,
                "failure_reason": failure_reason,
                **context,
            },
        ),
    )


def complete_quest(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    completion_input: QuestCompletionInput,
) -> QuestCompletionResult:
    """Complete a quest and write all M4 learner-state side effects atomically."""
    with transaction(database_connection):
        membership = _require_membership(
            database_connection,
            completion_input.handle,
            catalog.course.id,
        )
        quest = catalog.quest(completion_input.quest_id)
        _require_matching_passed_attempt(
            database_connection,
            completion_input.handle,
            catalog.course.id,
            completion_input.quest_id,
            completion_input.attempt_id,
        )
        existing_completion = get_quest_completion(
            database_connection,
            completion_input.handle,
            catalog.course.id,
            completion_input.quest_id,
        )
        if existing_completion is not None:
            return QuestCompletionResult(
                completion=existing_completion,
                completed_now=False,
                score_total=total_score_for_course(
                    database_connection,
                    completion_input.handle,
                    catalog.course.id,
                ),
                tier_promotions=(),
            )
        _require_current_assignment(
            database_connection,
            catalog,
            membership,
            completion_input.quest_id,
        )

        previous_score_total = total_score_for_course(
            database_connection,
            completion_input.handle,
            catalog.course.id,
        )
        complete_quest_repository(
            database_connection,
            QuestCompletion(
                handle=completion_input.handle,
                course_id=catalog.course.id,
                quest_id=completion_input.quest_id,
                attempt_id=completion_input.attempt_id,
                completed_at=completion_input.completed_at,
                source=completion_input.source,
            ),
        )
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle=completion_input.handle,
                course_id=catalog.course.id,
                amount=quest.score,
                reason="quest_completed",
                related_type="quest",
                related_id=completion_input.quest_id,
                created_at=completion_input.completed_at,
            ),
        )
        speed_bonus = (
            _speed_bonus(
                count_rank_eligible_quest_completions(
                    database_connection,
                    catalog.course.id,
                    completion_input.quest_id,
                ),
            )
            if membership.rank_eligible
            else 0
        )
        if speed_bonus:
            add_score_entry(
                database_connection,
                ScoreLedgerEntry(
                    id=None,
                    handle=completion_input.handle,
                    course_id=catalog.course.id,
                    amount=speed_bonus,
                    reason="quest_completion_speed_bonus",
                    related_type="quest",
                    related_id=completion_input.quest_id,
                    created_at=completion_input.completed_at,
                ),
            )
        score_total = total_score_for_course(
            database_connection,
            completion_input.handle,
            catalog.course.id,
        )
        tier_promotions = record_tier_promotions(
            database_connection,
            catalog,
            completion_input.handle,
            completion_input.completed_at,
            completion_input.source,
            previous_score_total,
            score_total,
        )
        completion_effects = _CompletedQuestEffects(
            quest=quest,
            score_total=score_total,
            score_awarded=quest.score + speed_bonus,
            tier_promotions=tier_promotions,
        )
        _append_completion_audit_events(
            database_connection,
            catalog,
            completion_input,
            completion_effects,
        )
        _enqueue_projection(
            database_connection,
            completion_input.handle,
            catalog.course.id,
            completion_input.completed_at,
            "quest_completed",
        )
        return QuestCompletionResult(
            completion=_require_completion(
                database_connection,
                completion_input.handle,
                catalog.course.id,
                completion_input.quest_id,
            ),
            completed_now=True,
            score_total=score_total,
            tier_promotions=tier_promotions,
        )


def _speed_bonus(completion_count: int) -> int:
    return _SPEED_BONUSES[completion_count - 1] if completion_count <= len(_SPEED_BONUSES) else 0


def _session_objective_related_id(session_id: str, objective_id: str) -> str:
    return f"{session_id}:{objective_id}"


def _current_assigned_incomplete_quest(
    catalog: CourseCatalog,
    session_reached: str,
    assignments: list[QuestAssignment],
    completed_quest_ids: frozenset[str],
) -> Quest | None:
    return _current_quest(
        catalog,
        session_reached,
        *(
            catalog.quest(assignment.quest_id)
            for assignment in assignments
            if assignment.quest_id not in completed_quest_ids
        ),
    )


def _current_quest(
    catalog: CourseCatalog,
    session_reached: str,
    *quests: Quest | None,
) -> Quest | None:
    prioritized_quests = catalog.prioritized_quests(
        session_reached,
        tuple(quest for quest in quests if quest is not None),
    )
    return prioritized_quests[0] if prioritized_quests else None


def _assignments_available_after_session(
    catalog: CourseCatalog,
    assignments: list[QuestAssignment],
    session_reached: str,
) -> list[QuestAssignment]:
    available_quest_ids = frozenset(
        quest.id for quest in catalog.quests_available_through(session_reached)
    )
    return [assignment for assignment in assignments if assignment.quest_id in available_quest_ids]


def record_tier_promotions(  # noqa: PLR0913 - Score awards supply the promotion context.
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    handle: str,
    promoted_at: str,
    source: str,
    previous_score_total: int,
    score_total: int,
) -> tuple[TierPromotion, ...]:
    """Record and audit tiers newly crossed by a score award."""
    recorded_tier_ids = frozenset(
        promotion.tier_id
        for promotion in list_tier_promotions(
            database_connection,
            handle,
            catalog.course.id,
        )
    )
    promotions = tuple(
        TierPromotion(
            handle=handle,
            course_id=catalog.course.id,
            tier_id=tier.id,
            promoted_at=promoted_at,
            score_total=score_total,
        )
        for tier in crossed_tiers(catalog, previous_score_total, score_total)
        if tier.id not in recorded_tier_ids
    )
    for promotion in promotions:
        record_tier_promotion(database_connection, promotion)
    for promotion in promotions:
        append_audit_event(
            database_connection,
            AuditEvent(
                event_type="tier_promoted",
                handle=handle,
                source=source,
                created_at=promoted_at,
                payload={
                    "course_id": catalog.course.id,
                    "tier_id": promotion.tier_id,
                    "score_total": promotion.score_total,
                },
            ),
        )
    return promotions


def _append_completion_audit_events(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    completion_input: QuestCompletionInput,
    completion_effects: _CompletedQuestEffects,
) -> None:
    append_audit_event(
        database_connection,
        AuditEvent(
            event_type="quest_completed",
            handle=completion_input.handle,
            source=completion_input.source,
            created_at=completion_input.completed_at,
            payload={
                "course_id": catalog.course.id,
                "quest_id": completion_effects.quest.id,
                "attempt_id": completion_input.attempt_id,
            },
        ),
    )
    append_audit_event(
        database_connection,
        AuditEvent(
            event_type="score_awarded",
            handle=completion_input.handle,
            source=completion_input.source,
            created_at=completion_input.completed_at,
            payload={
                "course_id": catalog.course.id,
                "quest_id": completion_effects.quest.id,
                "amount": completion_effects.score_awarded,
                "score_total": completion_effects.score_total,
            },
        ),
    )


def _enqueue_projection(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
    created_at: str,
    reason: ProjectionOutboxReason,
) -> None:
    enqueue_outbox_item(
        database_connection,
        projection_outbox_item(
            handle=handle,
            course_id=course_id,
            created_at=created_at,
            reason=reason,
        ),
    )


def _require_membership(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
) -> CohortMembership:
    membership = get_membership(database_connection, handle, course_id)
    if membership is None:
        raise ProgressServiceError("learner is not enrolled in this course")
    return membership


def _require_course_release(
    database_connection: sqlite3.Connection,
    course_id: str,
) -> CourseRelease | None:
    """Return the release state needed for gated course work."""
    return get_course_release(database_connection, course_id)


def _require_assignment(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
    quest_id: str,
) -> QuestAssignment:
    assignment = get_assignment(database_connection, handle, course_id, quest_id)
    if assignment is None:
        raise ProgressServiceError("quest assignment was not written")
    return assignment


def _require_current_assignment(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    membership: CohortMembership,
    quest_id: str,
) -> QuestAssignment:
    course_release = _require_course_release(database_connection, membership.course_id)
    if course_release is None:
        raise ProgressServiceError("learner has not reached a course session")
    assignment = get_assignment(
        database_connection,
        membership.handle,
        membership.course_id,
        quest_id,
    )
    if assignment is None:
        raise ProgressServiceError("quest is not assigned")
    if (
        current_session_objective(
            database_connection,
            catalog,
            handle=membership.handle,
        ).objective
        is not None
    ):
        raise ProgressServiceError("released session objectives are incomplete")
    completed_quest_ids = list_completed_quest_ids(
        database_connection,
        membership.handle,
        membership.course_id,
    )
    current_assigned_quest = _current_assigned_incomplete_quest(
        catalog,
        course_release.session_reached,
        _assignments_available_after_session(
            catalog,
            list_assignments(database_connection, membership.handle, membership.course_id),
            course_release.session_reached,
        ),
        completed_quest_ids,
    )
    next_quest = catalog.next_assignable_quest(
        course_release.session_reached,
        completed_quest_ids,
    )
    selected_quest = _current_quest(
        catalog,
        course_release.session_reached,
        current_assigned_quest,
        next_quest,
    )
    if selected_quest is None or selected_quest.id != quest_id:
        raise ProgressServiceError("quest is not currently available")
    return assignment


def _require_attempt(database_connection: sqlite3.Connection, attempt_id: int) -> QuestAttempt:
    attempt = get_quest_attempt(database_connection, attempt_id)
    if attempt is None:
        raise ProgressServiceError("quest attempt was not written")
    return attempt


def _require_matching_passed_attempt(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
    quest_id: str,
    attempt_id: int,
) -> None:
    attempt = _require_attempt(database_connection, attempt_id)
    if attempt.handle != handle or attempt.course_id != course_id or attempt.quest_id != quest_id:
        raise RepositoryError("quest completion attempt does not match completion")
    if attempt.outcome != "passed":
        raise RepositoryError("quest completion attempt did not pass")


def _require_completion(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
    quest_id: str,
) -> QuestCompletion:
    completion = get_quest_completion(database_connection, handle, course_id, quest_id)
    if completion is None:
        raise ProgressServiceError("quest completion was not written")
    return completion
