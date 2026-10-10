"""Prepare fresh S9 timer evidence through the authenticated learner CLI."""

from __future__ import annotations

from dataclasses import replace

from maker_guide.chat.contract import (
    ChatDependencies,
    ChatRequest,
    CliChatContext,
    PreparedTimerCheck,
)
from maker_guide.chat.intents import chat_intent
from maker_guide.curriculum.models import ArtifactCheckValidation
from maker_guide.progress.models import ProgressServiceError
from maker_guide.progress.service import current_session_objective
from maker_guide.timer_check import (
    parse_timer_check_report,
    read_timer_sources,
    source_digests,
    timer_check_report_payload,
)


def prepare_timer_check(
    request: ChatRequest, dependencies: ChatDependencies, learner_handle: str
) -> PreparedTimerCheck | None:
    """Prepare a one-shot, file-bound timer report before progress writes."""
    if (
        not isinstance(request.context, CliChatContext)
        or request.visibility != "private"
        or chat_intent(request.text) not in {"now", "check"}
        or dependencies.database_connection.in_transaction
    ):
        return None
    try:
        objective_result = current_session_objective(
            dependencies.database_connection,
            dependencies.catalog,
            handle=learner_handle,
        )
    except ProgressServiceError:
        objective_result = None
    objective = objective_result.objective if objective_result is not None else None
    if (
        objective_result is None
        or objective is None
        or not isinstance(objective.validation, ArtifactCheckValidation)
        or objective.validation.kind != "timer"
    ):
        return None
    prepared = PreparedTimerCheck(
        course_id=dependencies.catalog.course.id,
        session_id=objective_result.session_id,
        objective_id=objective.id,
        evidence_since=objective_result.evidence_since,
    )
    if dependencies.timer_check_runner is None:
        return replace(prepared, failure_reason="timer-check-unsupported-client")
    try:
        service, timer = read_timer_sources(
            learner_handle, account_lookup=dependencies.account_lookup
        )
        service_digest, timer_digest = source_digests(service, timer)
        report = dependencies.timer_check_runner(service_digest, timer_digest)
        parsed = parse_timer_check_report(
            timer_check_report_payload(report), service_digest, timer_digest
        )
        current_service, current_timer = read_timer_sources(
            learner_handle, account_lookup=dependencies.account_lookup
        )
    except (OSError, EOFError, ValueError):
        return replace(prepared, failure_reason="timer-check-failed")
    if source_digests(current_service, current_timer) != (service_digest, timer_digest):
        return replace(prepared, failure_reason="timer-check-stale")
    failure_reason = (
        "timer-check-stale"
        if parsed.error == "unit-changed"
        else "timer-check-unsafe-user"
        if parsed.error == "unsafe-user"
        else "timer-check-failed"
        if parsed.error is not None
        else None
    )
    return replace(prepared, report=parsed, failure_reason=failure_reason)
