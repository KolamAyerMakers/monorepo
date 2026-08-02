"""Deterministic progress-backed chat responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from maker_guide.chat.contract import ChatDependencies, ChatError, PreparedAnswerInterpretation
from maker_guide.chat.doc_selection import learner_document_path
from maker_guide.chat.presenter import (
    format_completed_quest,
    format_failed_check,
    format_today_quest,
)
from maker_guide.chat.snapshot import build_learner_snapshot
from maker_guide.progress.models import (
    CurrentSessionObjectiveResult,
    QuestAttemptInput,
    QuestCompletionInput,
)
from maker_guide.progress.service import (
    complete_quest,
    complete_session_objective,
    current_quest,
    current_session_objective,
    record_attempt,
    record_session_objective_validation_failure,
)
from maker_guide.progress.validation import (
    QuestValidationInput,
    QuestValidationResult,
    validate_quest,
    validate_session_objective,
    validation_answer_question,
)
from maker_guide.repositories.cohort_membership import get_membership
from maker_guide.repositories.session_objective_completion import list_completed_objective_ids
from maker_guide.repositories.tier_promotion import TierPromotion

IRC_CLIENT_VERIFICATION_FAILURE_REASON = "missing-irc-ctcp-version"
_NO_CURRENT_QUEST_TEXT = """All currently available quests are complete.

Ask again after the next session unlocks more work."""
_CONCEPT_ASSOCIATION_NUDGES = {
    "pipe-output-to-input": "how `cut`'s `stdout` becomes `wc`'s `stdin`",
    "stdout-descriptor": "`stdout` and its descriptor number",
    "stdin-descriptor": "`stdin` and its descriptor number",
    "stderr-descriptor": "`stderr` and its descriptor number",
    "left-to-right-redirection": "the order redirections are applied",
    "stderr-follows-stdout": "where `2>&1` sends `stderr`",
    "executable-file": "an executable program and where it exists",
    "running-process": "a process and its relationship to a running program",
    "reported-process-pair": "one labeled numeric PID and its command",
}


def progress_response(
    dependencies: ChatDependencies,
    learner_handle: str,
) -> str:
    """Format the learner's current recorded course progress."""
    learner_snapshot = build_learner_snapshot(
        dependencies.database_connection,
        dependencies.catalog,
        learner_handle,
    )
    completed_objective_count = sum(
        len(
            list_completed_objective_ids(
                dependencies.database_connection,
                learner_handle,
                dependencies.catalog.course.id,
                session.id,
            ),
        )
        for session in dependencies.catalog.course.sessions
    )
    response_parts = [
        "Progress:",
        f"Session: {learner_snapshot.current_session or 'Not available yet'}",
        f"Score: {learner_snapshot.score}",
        f"Tier: {learner_snapshot.tier or 'none'}",
        f"Objectives completed: {completed_objective_count}",
        f"Quests completed: {len(learner_snapshot.completed_quests)}",
    ]
    objective_result = (
        current_session_objective(
            dependencies.database_connection,
            dependencies.catalog,
            handle=learner_handle,
        )
        if learner_snapshot.current_session is not None
        and get_membership(
            dependencies.database_connection,
            learner_handle,
            dependencies.catalog.course.id,
        )
        is not None
        else None
    )
    if objective_result is not None and objective_result.objective is not None:
        objective_title = objective_result.objective.title
        response_parts.append(
            f"Current objective: {objective_title} ({objective_result.session_id})",
        )
    elif learner_snapshot.pending_quests:
        response_parts.append(
            f"Next quest: {dependencies.catalog.quest(learner_snapshot.pending_quests[0]).title}",
        )
    else:
        response_parts.append("Next quest: No released quests remaining.")
    response_parts.append("Next: guide now")
    return "\n".join(response_parts)


@dataclass(frozen=True, kw_only=True, slots=True)
class CheckResponse:
    """Deterministic check response plus transport retry metadata."""

    text: str
    retry_after_irc_client_verification: bool = False
    tier_promotions: tuple[TierPromotion, ...] = ()


def _current_quest_response(
    dependencies: ChatDependencies,
    learner_handle: str,
    source: str,
    timestamp: str,
) -> tuple[str, tuple[TierPromotion, ...]]:
    """Assign or return the current deterministic quest."""
    current_quest_result = current_quest(
        dependencies.database_connection,
        dependencies.catalog,
        handle=learner_handle,
        assigned_at=timestamp,
        source=source,
    )
    if current_quest_result.quest is None:
        return _NO_CURRENT_QUEST_TEXT, ()
    return format_today_quest(current_quest_result.quest), ()


def now_response(
    dependencies: ChatDependencies,
    learner_handle: str,
    source: str,
    timestamp: str,
) -> tuple[str, tuple[TierPromotion, ...]]:
    """Show the current objective or deterministically assigned quest without validation."""
    objective_result = current_session_objective(
        dependencies.database_connection,
        dependencies.catalog,
        handle=learner_handle,
    )
    if objective_result.objective is not None:
        return _format_session_objective(objective_result, dependencies), ()
    return _current_quest_response(dependencies, learner_handle, source, timestamp)


def check_response(  # noqa: PLR0911, PLR0913 - Routing supplies request context directly.
    dependencies: ChatDependencies,
    learner_handle: str,
    source: str,
    timestamp: str,
    answer_text: str | None = None,
    prepared_answer_interpretation: PreparedAnswerInterpretation | None = None,
    *,
    is_answer: bool,
) -> CheckResponse:
    """Run deterministic validation and record progress side effects."""
    objective_result = current_session_objective(
        dependencies.database_connection,
        dependencies.catalog,
        handle=learner_handle,
    )
    if objective_result.objective is not None:
        if prepared_answer_interpretation is not None and (
            prepared_answer_interpretation.target_type != "session_objective"
            or prepared_answer_interpretation.target_id != objective_result.objective.id
            or prepared_answer_interpretation.target_session_id != objective_result.session_id
        ):
            return CheckResponse(
                text=now_response(dependencies, learner_handle, source, timestamp)[0],
            )
        return _check_session_objective(
            dependencies,
            learner_handle,
            source,
            timestamp,
            answer_text,
            prepared_answer_interpretation,
            is_answer,
        )
    current_quest_result = current_quest(
        dependencies.database_connection,
        dependencies.catalog,
        handle=learner_handle,
        assigned_at=timestamp,
        source=source,
    )
    if current_quest_result.quest is None:
        return CheckResponse(text="There is no currently available quest to check.")
    if current_quest_result.assignment is None:
        raise ChatError("current quest assignment was not written")
    if prepared_answer_interpretation is not None and (
        prepared_answer_interpretation.target_type != "quest"
        or prepared_answer_interpretation.target_id != current_quest_result.quest.id
    ):
        return CheckResponse(text=format_today_quest(current_quest_result.quest))
    expects_answer = validation_answer_question(current_quest_result.quest.validation) is not None
    if expects_answer != is_answer or (answer_text is None and is_answer):
        return CheckResponse(text=format_today_quest(current_quest_result.quest))

    validation_result = validate_quest(
        QuestValidationInput(
            database_connection=dependencies.database_connection,
            catalog=dependencies.catalog,
            handle=learner_handle,
            quest=current_quest_result.quest,
            checked_at=timestamp,
            assigned_at=current_quest_result.assignment.assigned_at,
            answer_text=answer_text,
            answer_concept_assessments=(
                prepared_answer_interpretation.assessments
                if prepared_answer_interpretation is not None
                and prepared_answer_interpretation.target_type == "quest"
                and prepared_answer_interpretation.target_id == current_quest_result.quest.id
                else ()
            ),
            account_lookup=dependencies.account_lookup,
        ),
    )
    attempt_result = record_attempt(
        dependencies.database_connection,
        dependencies.catalog,
        QuestAttemptInput(
            handle=learner_handle,
            quest_id=current_quest_result.quest.id,
            attempted_at=timestamp,
            source=source,
            outcome="passed" if validation_result.passed else "failed",
            failure_reason=validation_result.failure_reason,
            evidence=validation_result.evidence,
        ),
    )
    if attempt_result.attempt.id is None:
        raise ChatError("quest attempt was not written")
    if not validation_result.passed:
        return CheckResponse(
            text=format_failed_check(
                current_quest_result.quest,
                validation_result,
                (
                    prepared_answer_interpretation.feedback
                    if prepared_answer_interpretation is not None
                    else None
                ),
            ),
            retry_after_irc_client_verification=(
                validation_result.failure_reason == IRC_CLIENT_VERIFICATION_FAILURE_REASON
            ),
        )
    return CheckResponse(
        text=format_completed_quest(
            dependencies.catalog,
            current_quest_result.quest,
            complete_quest(
                dependencies.database_connection,
                dependencies.catalog,
                QuestCompletionInput(
                    handle=learner_handle,
                    quest_id=current_quest_result.quest.id,
                    attempt_id=attempt_result.attempt.id,
                    completed_at=timestamp,
                    source=source,
                ),
            ),
        ),
    )


def _check_session_objective(  # noqa: PLR0913 - Chat routing supplies request context directly.
    dependencies: ChatDependencies,
    learner_handle: str,
    source: str,
    timestamp: str,
    answer_text: str | None,
    prepared_answer_interpretation: PreparedAnswerInterpretation | None,
    is_answer: bool,
) -> CheckResponse:
    """Validate a current practical or answer-bearing session objective."""
    objective_result = current_session_objective(
        dependencies.database_connection,
        dependencies.catalog,
        handle=learner_handle,
    )
    if objective_result.objective is None:
        raise ChatError("current session objective was not found")
    objective = objective_result.objective
    expects_answer = validation_answer_question(objective.validation) is not None
    if (is_answer and not expects_answer) or (answer_text is None and is_answer):
        return CheckResponse(text=now_response(dependencies, learner_handle, source, timestamp)[0])
    validation_result = validate_session_objective(
        QuestValidationInput(
            database_connection=dependencies.database_connection,
            catalog=dependencies.catalog,
            handle=learner_handle,
            checked_at=timestamp,
            assigned_at=objective_result.evidence_since,
            answer_text=answer_text,
            answer_concept_assessments=(
                prepared_answer_interpretation.assessments
                if prepared_answer_interpretation is not None
                and prepared_answer_interpretation.target_type == "session_objective"
                and prepared_answer_interpretation.target_id == objective.id
                and prepared_answer_interpretation.target_session_id == objective_result.session_id
                else ()
            ),
            account_lookup=dependencies.account_lookup,
        ),
        objective.validation,
    )
    if not validation_result.passed:
        record_session_objective_validation_failure(
            dependencies.database_connection,
            dependencies.catalog,
            handle=learner_handle,
            session_id=objective_result.session_id,
            objective_id=objective.id,
            failed_at=timestamp,
            source=source,
            validation_result=validation_result,
        )
        return CheckResponse(
            text=_format_session_objective(
                objective_result,
                dependencies,
                validation_result,
                (
                    prepared_answer_interpretation.feedback
                    if prepared_answer_interpretation is not None
                    else None
                ),
            ),
        )
    completion_result = complete_session_objective(
        dependencies.database_connection,
        dependencies.catalog,
        handle=learner_handle,
        session_id=objective_result.session_id,
        objective_id=objective.id,
        completed_at=timestamp,
        evidence=validation_result.evidence,
        source=source,
    )
    return CheckResponse(
        text=(
            "\n\n".join(
                (
                    f"Answer accepted. Objective complete: {objective.title}.",
                    "Next:",
                    now_response(dependencies, learner_handle, source, timestamp)[0],
                ),
            )
            if is_answer
            else now_response(dependencies, learner_handle, source, timestamp)[0]
        ),
        tier_promotions=completion_result.tier_promotions,
    )


def _format_session_objective(
    objective_result: CurrentSessionObjectiveResult,
    dependencies: ChatDependencies,
    validation_result: QuestValidationResult | None = None,
    tutor_feedback: str | None = None,
) -> str:
    """Format a practical session objective and its incomplete evidence."""
    objective = objective_result.objective
    if objective is None:
        raise ChatError("current session objective was not found")
    response_parts = [
        f"Current session objective: {objective.title}",
        f"Start here:\n{objective.prompt}",
    ]
    self_study_reference = next(
        (
            reference
            for reference in dependencies.catalog.session(objective_result.session_id).content
            if reference.purpose == "self-study"
        ),
        None,
    )
    if self_study_reference is not None:
        response_parts.append(
            "\n".join(
                (
                    "Read self-study guide:",
                    f"glow -p {learner_document_path(self_study_reference.path)}",
                ),
            ),
        )
    if validation_result is not None:
        if (
            validation_result.failure_reason == "missing-answer"
            and (answer_question := validation_answer_question(objective.validation)) is not None
        ):
            response_parts.append(
                " ".join(
                    (
                        "The practical evidence is ready. Now answer this question in your own",
                        f"words with `guide answer 'your explanation'`:\n{answer_question}",
                    ),
                ),
            )
        else:
            response_parts.append(_objective_status(validation_result, tutor_feedback))
    return "\n\n".join(response_parts)


def _objective_status(
    validation_result: QuestValidationResult,
    tutor_feedback: str | None = None,
) -> str:
    """Format concise missing evidence for a session objective."""
    missing_commands = _objective_evidence_strings(validation_result, "missing_commands")
    if missing_commands:
        if (
            _objective_evidence_strings(validation_result, "matched_concept_ids")
            and not _objective_evidence_strings(validation_result, "missing_concept_ids")
            and not _objective_evidence_strings(validation_result, "contradicted_concept_ids")
        ):
            return "".join(
                (
                    "Your answer is correct, but the practical step is still missing. Run ",
                    ", ".join(f"`{command}`" for command in missing_commands),
                    ", then send your answer once more to complete the objective.",
                ),
            )
        return "".join(
            (
                "I need to see this command before I can verify the objective: ",
                ", ".join(f"`{command}`" for command in missing_commands),
            ),
        )
    if tutor_feedback is not None and validation_result.failure_reason in {
        "missing-concept",
        "contradicted-concept",
    }:
        return f"Let's work through your answer:\n{tutor_feedback}"
    concept_nudges = tuple(
        _CONCEPT_ASSOCIATION_NUDGES[concept_id]
        for concept_id in _objective_evidence_strings(
            validation_result,
            (
                "contradicted_concept_ids"
                if validation_result.failure_reason == "contradicted-concept"
                else "missing_concept_ids"
            ),
        )
        if concept_id in _CONCEPT_ASSOCIATION_NUDGES
    )
    if concept_nudges:
        return (
            "One part of that answer conflicts with the concept. Recheck "
            + "; ".join(concept_nudges)
            + ". What would you change?"
            if validation_result.failure_reason == "contradicted-concept"
            else "".join(
                (
                    "I can't connect that answer to the full idea yet. ",
                    "In your own words, explain ",
                    "; ".join(concept_nudges),
                    ".",
                ),
            )
        )
    return "I cannot verify that yet. Do the objective, then run `guide now`."


def _objective_evidence_strings(
    validation_result: QuestValidationResult,
    key: str,
) -> tuple[str, ...]:
    """Return string evidence from a result or its immediate child checks."""
    evidence_value = validation_result.evidence.get(key)
    if isinstance(evidence_value, list):
        return tuple(item for item in cast("list[object]", evidence_value) if isinstance(item, str))
    checks = validation_result.evidence.get("checks")
    if not isinstance(checks, list):
        return ()
    for check in cast("list[object]", checks):
        if not isinstance(check, dict):
            continue
        evidence_value = cast("dict[str, object]", check).get(key)
        if isinstance(evidence_value, list):
            return tuple(
                item for item in cast("list[object]", evidence_value) if isinstance(item, str)
            )
    return ()
