"""Read-only LLM tutor chat support and audit persistence."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from textwrap import dedent
from typing import cast

from maker_guide.chat.contract import (
    ChatDependencies,
    ChatRequest,
    CliChatContext,
    ResponseDraft,
    RestrictedLlmAuditLogInput,
    TutorAuditEvent,
)
from maker_guide.chat.doc_selection import (
    TutorDocSelectionInput,
    quest_doc_contexts,
    select_tutor_docs,
)
from maker_guide.chat.intents import chat_intent
from maker_guide.chat.snapshot import build_learner_snapshot
from maker_guide.curriculum.models import CourseCatalog, Quest
from maker_guide.llm_tutor import (
    ReadOnlyCommandObservation,
    ReadOnlyInteractionContext,
    ReadOnlyLearnerState,
    ReadOnlyObjectiveContext,
    ReadOnlyQuestContext,
    ReadOnlySessionContext,
    ReadOnlyTutorContext,
    ReadOnlyValidationStatus,
    TutorError,
    TutorRateLimitError,
    TutorRequest,
    TutorResponse,
    build_tutor_messages,
    safe_tutor_text,
)
from maker_guide.progress.service import current_session_objective
from maker_guide.progress.validation import (
    QuestValidationInput,
    validate_quest,
    validation_answer_question,
)
from maker_guide.repositories.audit_event import AuditEvent, append_audit_event
from maker_guide.repositories.cohort_membership import get_membership
from maker_guide.repositories.command_observation import list_recent_command_observations
from maker_guide.repositories.help_interaction import list_recent_help_interactions
from maker_guide.repositories.helpers import transaction
from maker_guide.repositories.llm_audit_log import LlmAuditLog, append_llm_audit_log
from maker_guide.repositories.quest_assignment import get_assignment
from maker_guide.retention import llm_audit_expires_at

_FREEFORM_TUTOR_DISABLED_TEXT = (
    dedent(
        """\
    I can't do open-ended tutoring here yet. Run `guide now` for your current quest,
    `guide check` when you've tried it, or `guide answer 'your answer'` when the
    quest asks a question.
    """,
    )
    .replace("\n", " ")
    .strip()
)
_RECENT_INTERACTION_LIMIT = 4
_RECENT_INTERACTION_TEXT_LIMIT = 1_200
_QUESTION_PREFIXES = (
    "are ",
    "can ",
    "could ",
    "do ",
    "does ",
    "explain ",
    "how ",
    "is ",
    "tell me ",
    "what ",
    "when ",
    "where ",
    "who ",
    "why ",
)


def calls_private_tutor(
    request: ChatRequest,
    dependencies: ChatDependencies,
    learner_handle: str,
) -> bool:
    """Return whether handling will call the private tutor before opening a transaction."""
    return (
        dependencies.tutor_client is not None
        and request.visibility == "private"
        and chat_intent(request.text) == "freeform"
        and not routes_bare_interactive_answer(request, dependencies, learner_handle)
    )


def routes_bare_interactive_answer(
    request: ChatRequest,
    dependencies: ChatDependencies,
    learner_handle: str,
) -> bool:
    """Return whether free-form text should be treated as the current quest answer."""
    if chat_intent(request.text) != "freeform" or _is_question(request.text):
        return False
    learner_snapshot = build_learner_snapshot(
        dependencies.database_connection,
        dependencies.catalog,
        learner_handle,
    )
    if learner_snapshot.current_session is None:
        return False
    objective_result = current_session_objective(
        dependencies.database_connection,
        dependencies.catalog,
        handle=learner_handle,
    )
    if objective_result.objective is not None:
        return validation_answer_question(objective_result.objective.validation) is not None
    if not learner_snapshot.pending_quests:
        return False
    return (
        validation_answer_question(
            dependencies.catalog.quest(learner_snapshot.pending_quests[0]).validation,
        )
        is not None
    )


def _is_question(text: str) -> bool:
    return "?" in text or text.casefold().lstrip().startswith(_QUESTION_PREFIXES)


def freeform_response_draft(
    request: ChatRequest,
    dependencies: ChatDependencies,
    learner_handle: str,
    timestamp: str,
) -> ResponseDraft:
    """Build a response draft for free-form learner text."""
    if dependencies.tutor_client is None:
        return _freeform_tutor_disabled_draft()
    if request.visibility == "public":
        return ResponseDraft(
            text="Ask me privately for tutoring so I do not expose your learner state in public.",
            topic_tags=("privacy",),
        )
    return _tutor_response_draft(request, dependencies, learner_handle, timestamp)


def build_read_only_tutor_context(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    request: ChatRequest,
    handle: str,
    timestamp: str,
) -> ReadOnlyTutorContext:
    """Build immutable tutor context without exposing mutation handles."""
    learner_snapshot = build_learner_snapshot(database_connection, catalog, handle)
    objective_result = (
        current_session_objective(database_connection, catalog, handle=handle)
        if learner_snapshot.current_session is not None
        and get_membership(database_connection, handle, catalog.course.id) is not None
        else None
    )
    focused_pending_quest_ids = learner_snapshot.pending_quests
    if objective_result is not None and objective_result.objective is not None:
        focused_pending_quest_ids = ()
    elif focused_pending_quest_ids:
        focused_session_id = catalog.quest(
            focused_pending_quest_ids[0],
        ).available_after_session
        focused_pending_quest_ids = tuple(
            quest_id
            for quest_id in focused_pending_quest_ids
            if catalog.quest(quest_id).available_after_session == focused_session_id
        )
    return ReadOnlyTutorContext(
        course_title=catalog.course.title,
        course_system_prompt=catalog.course.tutor_system_prompt,
        learner=ReadOnlyLearnerState(
            handle=learner_snapshot.handle,
            course_id=learner_snapshot.course_id,
            current_session=learner_snapshot.current_session,
            taught_commands=learner_snapshot.taught_commands,
            taught_skills=learner_snapshot.taught_skills,
            pending_quests=focused_pending_quest_ids,
            completed_quests=learner_snapshot.completed_quests,
            score=learner_snapshot.score,
            tier=learner_snapshot.tier,
            recent_help_topics=learner_snapshot.recent_help_topics,
        ),
        current_objective=None
        if objective_result is None or objective_result.objective is None
        else ReadOnlyObjectiveContext(
            session_id=objective_result.session_id,
            objective_id=objective_result.objective.id,
            title=objective_result.objective.title,
            prompt=objective_result.objective.prompt,
        ),
        quests=tuple(
            _read_only_quest_context(catalog.quest(quest_id))
            for quest_id in focused_pending_quest_ids[:3]
        ),
        docs=select_tutor_docs(
            TutorDocSelectionInput(
                catalog=catalog,
                current_session_id=(
                    objective_result.session_id
                    if objective_result is not None and objective_result.objective is not None
                    else learner_snapshot.current_session
                ),
                pending_quests=focused_pending_quest_ids,
                message=request.text,
            ),
        ),
        recent_commands=tuple(
            ReadOnlyCommandObservation(
                command=observation.command,
                cwd=observation.cwd,
                observed_at=observation.observed_at,
            )
            for observation in list_recent_command_observations(
                database_connection,
                handle,
                catalog.course.id,
                (datetime.now(UTC) - timedelta(hours=2))
                .isoformat(timespec="seconds")
                .replace("+00:00", "Z"),
                10,
                observed_through=timestamp,
            )
        ),
        recent_interactions=tuple(
            ReadOnlyInteractionContext(
                question=_bounded_interaction_text(interaction.question),
                response=_bounded_interaction_text(interaction.response or ""),
                created_at=interaction.created_at,
            )
            # ponytail: four turns cover follow-ups; add summaries only if that proves too short.
            for interaction in reversed(
                list_recent_help_interactions(
                    database_connection,
                    handle,
                    _RECENT_INTERACTION_LIMIT,
                    source=request.context.source,
                    visibility="private",
                )
            )
        ),
        validation_status=_read_only_validation_status(
            database_connection,
            catalog,
            handle,
            timestamp,
            focused_pending_quest_ids,
        ),
        session=ReadOnlySessionContext(
            terminal=request.context.terminal
            if isinstance(request.context, CliChatContext)
            else None,
            ssh_connection=request.context.ssh_connection
            if isinstance(request.context, CliChatContext)
            else None,
            source=request.context.source,
        ),
    )


def _bounded_interaction_text(text: str) -> str:
    if len(text) <= _RECENT_INTERACTION_TEXT_LIMIT:
        return text
    return f"{text[: _RECENT_INTERACTION_TEXT_LIMIT - 3]}..."


def append_response_draft_side_effects(
    dependencies: ChatDependencies,
    learner_handle: str,
    source: str,
    timestamp: str,
    response_draft: ResponseDraft,
) -> None:
    """Persist restricted tutor audit side effects for a response draft."""
    if response_draft.restricted_llm_audit_log is not None:
        _append_restricted_llm_audit_log(
            dependencies,
            learner_handle,
            source,
            timestamp,
            response_draft.restricted_llm_audit_log,
        )
    if response_draft.tutor_audit_event is not None:
        _append_tutor_audit_event(dependencies, response_draft.tutor_audit_event)


def _tutor_response_draft(
    request: ChatRequest,
    dependencies: ChatDependencies,
    learner_handle: str,
    timestamp: str,
) -> ResponseDraft:
    if dependencies.tutor_client is None:
        return _freeform_tutor_disabled_draft()
    tutor_request = TutorRequest(
        bot_name=dependencies.bot_name,
        learner_handle=learner_handle,
        message=request.text,
        visibility="private",
        context=build_read_only_tutor_context(
            dependencies.database_connection,
            dependencies.catalog,
            request,
            learner_handle,
            timestamp,
        ),
        max_tokens=dependencies.tutor_max_tokens,
    )
    request_payload = _llm_request_payload(tutor_request)
    try:
        tutor_response = dependencies.tutor_client.answer(
            tutor_request,
            dependencies.response_chunk_writer,
        )
    except TutorRateLimitError:
        return ResponseDraft(
            text="Tutor rate limit reached. Try again in a minute.",
            topic_tags=("llm", "rate-limit"),
            restricted_llm_audit_log=RestrictedLlmAuditLogInput(
                provider="unavailable",
                model="unavailable",
                status="rate_limited",
                request_payload=request_payload,
                response_payload={"reason": "rate-limit"},
            ),
            tutor_audit_event=TutorAuditEvent(
                learner_handle=learner_handle,
                source=request.context.source,
                timestamp=timestamp,
                event_type="llm_tutor_rate_limited",
                payload={"course_id": dependencies.catalog.course.id},
            ),
        )
    except TutorError as error:
        return ResponseDraft(
            text="I can't reach my remote brain right now. Try me again in a moment.",
            topic_tags=("llm", "failure"),
            restricted_llm_audit_log=RestrictedLlmAuditLogInput(
                provider="unavailable",
                model="unavailable",
                status="failed",
                request_payload=request_payload,
                response_payload={"reason": str(error)},
            ),
            tutor_audit_event=TutorAuditEvent(
                learner_handle=learner_handle,
                source=request.context.source,
                timestamp=timestamp,
                event_type="llm_tutor_failed",
                payload={"course_id": dependencies.catalog.course.id, "reason": str(error)},
            ),
        )
    displayed_text = safe_tutor_text(tutor_response.text)
    return ResponseDraft(
        text=displayed_text,
        topic_tags=("llm", *tutor_response.topic_tags),
        restricted_llm_audit_log=RestrictedLlmAuditLogInput(
            provider=tutor_response.provider,
            model=tutor_response.model,
            status="answered",
            request_payload=request_payload,
            response_payload={
                "displayed_text": displayed_text,
                "raw_text": tutor_response.raw_text or tutor_response.text,
                "topic_tags": list(tutor_response.topic_tags),
            },
        ),
        tutor_audit_event=_tutor_answered_event(
            dependencies,
            learner_handle,
            request.context.source,
            timestamp,
            tutor_response,
        ),
    )


def _freeform_tutor_disabled_draft() -> ResponseDraft:
    return ResponseDraft(
        text=_FREEFORM_TUTOR_DISABLED_TEXT,
        topic_tags=("freeform", "guidance"),
    )


def _read_only_quest_context(quest: Quest) -> ReadOnlyQuestContext:
    return ReadOnlyQuestContext(
        quest_id=quest.id,
        available_after_session=quest.available_after_session,
        title=quest.title,
        learner_goal=quest.learner_goal,
        prompt=quest.prompt,
        first_hint=None if not quest.hints else quest.hints[0].text,
        docs=quest_doc_contexts(quest),
    )


def _read_only_validation_status(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    handle: str,
    timestamp: str,
    pending_quest_ids: tuple[str, ...],
) -> ReadOnlyValidationStatus | None:
    if not pending_quest_ids:
        return None
    assignment = get_assignment(
        database_connection,
        handle,
        catalog.course.id,
        pending_quest_ids[0],
    )
    if assignment is None:
        return None
    validation_result = validate_quest(
        QuestValidationInput(
            database_connection=database_connection,
            catalog=catalog,
            handle=handle,
            quest=catalog.quest(assignment.quest_id),
            checked_at=timestamp,
            assigned_at=assignment.assigned_at,
        ),
    )
    return ReadOnlyValidationStatus(
        quest_id=assignment.quest_id,
        passed=validation_result.passed,
        failure_reason=validation_result.failure_reason,
        evidence=validation_result.evidence,
    )


def _tutor_answered_event(
    dependencies: ChatDependencies,
    learner_handle: str,
    source: str,
    timestamp: str,
    tutor_response: TutorResponse,
) -> TutorAuditEvent:
    return TutorAuditEvent(
        learner_handle=learner_handle,
        source=source,
        timestamp=timestamp,
        event_type="llm_tutor_answered",
        payload={
            "course_id": dependencies.catalog.course.id,
            "model": tutor_response.model,
            "provider": tutor_response.provider,
            "response_chars": len(tutor_response.text),
            "topic_tags": list(tutor_response.topic_tags),
        },
    )


def _append_tutor_audit_event(
    dependencies: ChatDependencies,
    tutor_audit_event: TutorAuditEvent,
) -> None:
    with transaction(dependencies.database_connection):
        append_audit_event(
            dependencies.database_connection,
            AuditEvent(
                event_type=tutor_audit_event.event_type,
                handle=tutor_audit_event.learner_handle,
                source=tutor_audit_event.source,
                created_at=tutor_audit_event.timestamp,
                payload=tutor_audit_event.payload,
            ),
        )


def _append_restricted_llm_audit_log(
    dependencies: ChatDependencies,
    learner_handle: str,
    source: str,
    timestamp: str,
    audit_log_input: RestrictedLlmAuditLogInput,
) -> None:
    with transaction(dependencies.database_connection):
        append_llm_audit_log(
            dependencies.database_connection,
            LlmAuditLog(
                id=None,
                handle=learner_handle,
                course_id=dependencies.catalog.course.id,
                source=source,
                created_at=timestamp,
                provider=audit_log_input.provider,
                model=audit_log_input.model,
                status=audit_log_input.status,
                request=audit_log_input.request_payload,
                response=audit_log_input.response_payload,
                expires_at=llm_audit_expires_at(timestamp),
            ),
        )


def _llm_request_payload(tutor_request: TutorRequest) -> dict[str, object]:
    return {
        "max_tokens": tutor_request.max_tokens,
        "messages": cast("object", build_tutor_messages(tutor_request)),
    }
