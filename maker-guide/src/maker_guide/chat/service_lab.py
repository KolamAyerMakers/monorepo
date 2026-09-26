"""Prepare one learner-side fault or inspection outside progress transactions."""

from __future__ import annotations

import uuid
from dataclasses import replace
from typing import cast

from maker_guide.chat.contract import (
    ChatDependencies,
    ChatRequest,
    CliChatContext,
    PreparedServiceLab,
)
from maker_guide.chat.intents import chat_intent
from maker_guide.curriculum.models import ServiceLabValidation
from maker_guide.progress.models import ProgressServiceError
from maker_guide.progress.service import current_session_objective
from maker_guide.repositories.helpers import transaction
from maker_guide.repositories.service_lab_attempt import (
    ServiceLabAttempt,
    get_attempt,
    mark_started,
    reserve_attempt,
)
from maker_guide.service_lab import (
    ServiceLabAction,
    ServiceLabReport,
    parse_service_lab_report,
    service_lab_report_payload,
)

_MESSAGES = (
    "Your website had a small accident. The accident was me. Sorry.",
    "I tried to improve your website. It was working before, so technically I made a change.",
    (
        'Good news: your files are safe. Bad news: I have been "helping" again. '
        "Sorry about the website."
    ),
    (
        "Remember when your website worked? Those were good times. "
        "Anyway, this is troubleshooting now."
    ),
    "I touched something. Something stopped working. These events may be related. Sorry.",
    "I found an opportunity to help. My apologies. You may need to fix my contribution.",
)


def prepare_service_lab(  # noqa: PLR0911 - gate mutation and bind its fresh result in one place
    request: ChatRequest,
    dependencies: ChatDependencies,
    learner_handle: str,
    timestamp: str,
) -> PreparedServiceLab | None:
    """Reserve before execution; retries use the same run, never a new fault."""
    if (
        not isinstance(request.context, CliChatContext)
        or request.visibility != "private"
        or chat_intent(request.text) not in {"now", "check", "answer", "freeform"}
        or dependencies.service_lab_runner is None
        or dependencies.database_connection.in_transaction
    ):
        return None
    try:
        current = current_session_objective(
            dependencies.database_connection, dependencies.catalog, handle=learner_handle
        )
    except ProgressServiceError:
        return None
    if current.objective is None or not isinstance(
        current.objective.validation, ServiceLabValidation
    ):
        return None
    attempt = get_attempt(
        dependencies.database_connection,
        learner_handle,
        dependencies.catalog.course.id,
        current.session_id,
        current.objective.id,
    )
    if attempt is None:
        if chat_intent(request.text) != "now":
            return None
        with transaction(dependencies.database_connection):
            reserve_attempt(
                dependencies.database_connection,
                ServiceLabAttempt(
                    handle=learner_handle,
                    course_id=dependencies.catalog.course.id,
                    session_id=current.session_id,
                    objective_id=current.objective.id,
                    run_id=uuid.uuid4().hex,
                    scenario=current.objective.validation.scenario,
                    message_index=0,
                    created_at=timestamp,
                ),
            )
            attempt = get_attempt(
                dependencies.database_connection,
                learner_handle,
                dependencies.catalog.course.id,
                current.session_id,
                current.objective.id,
            )
    if attempt is None or attempt.scenario != current.objective.validation.scenario:
        return None
    prepared = PreparedServiceLab(
        course_id=attempt.course_id,
        session_id=attempt.session_id,
        objective_id=attempt.objective_id,
        evidence_since=current.evidence_since,
        action=ServiceLabAction(
            run_id=attempt.run_id,
            scenario=attempt.scenario,
            operation=(
                "start"
                if attempt.started_at is None and chat_intent(request.text) == "now"
                else "inspect"
            ),
        ),
    )
    try:
        report = cast("object", dependencies.service_lab_runner(prepared.action))
        report = (
            parse_service_lab_report(service_lab_report_payload(report), prepared.action)
            if isinstance(report, ServiceLabReport)
            else None
        )
    except (OSError, EOFError, ValueError):
        report = None
    if report is None:
        return replace(
            prepared, failure_reason="The local check could not finish. Run `guide now` again."
        )
    with transaction(dependencies.database_connection):
        current_after = current_session_objective(
            dependencies.database_connection, dependencies.catalog, handle=learner_handle
        )
        if (
            current_after.objective is None
            or current_after.objective.id != prepared.objective_id
            or current_after.session_id != prepared.session_id
            or current_after.evidence_since != prepared.evidence_since
        ):
            return replace(
                prepared, failure_reason="Your current task changed. Run `guide now` again."
            )
        first_started = report.started and mark_started(
            dependencies.database_connection, attempt.run_id, timestamp
        )
    return replace(
        prepared,
        report=report,
        # ponytail: a stable byte sum is enough variety for jokes, not a cryptographic hash.
        launch_message=(
            _MESSAGES[(sum(learner_handle.encode()) + attempt.message_index) % len(_MESSAGES)]
            if first_started and not report.healthy and report.error is None
            else None
        ),
    )


def current_lab_report(
    dependencies: ChatDependencies, learner_handle: str
) -> ServiceLabReport | None:
    """Never pass a report from another task/run or an older invocation to validation."""
    prepared = dependencies.service_lab_result
    if prepared is None or prepared.failure_reason is not None:
        return None
    current = current_session_objective(
        dependencies.database_connection, dependencies.catalog, handle=learner_handle
    )
    if (
        current.objective is None
        or not isinstance(current.objective.validation, ServiceLabValidation)
        or (
            dependencies.catalog.course.id,
            current.session_id,
            current.objective.id,
            current.evidence_since,
            current.objective.validation.scenario,
        )
        != (
            prepared.course_id,
            prepared.session_id,
            prepared.objective_id,
            prepared.evidence_since,
            prepared.action.scenario,
        )
    ):
        return None
    attempt = get_attempt(
        dependencies.database_connection,
        learner_handle,
        prepared.course_id,
        prepared.session_id,
        prepared.objective_id,
    )
    if attempt is None or attempt.run_id != prepared.action.run_id:
        return None
    return prepared.report


def lab_status_text(prepared: PreparedServiceLab | None) -> str:
    """Keep deterministic status helpful without revealing the injected fault."""
    if prepared is not None and prepared.failure_reason is not None:
        return prepared.failure_reason
    if prepared is None or prepared.report is None:
        return (
            "Run `guide now` in your SSH terminal to start or inspect this challenge."
            if prepared is None
            else "I could not inspect your service. Run `guide now` in your SSH terminal."
        )
    report = prepared.report
    if report.error is not None:
        return {
            "baseline-unhealthy": (
                "Your site must work before I can start this challenge. "
                "Check its status and page, then run `guide now`."
            ),
            "unsafe-unit": (
                "This unit differs from the course setup. Check the self-study guide; "
                "I have not started another fault."
            ),
            "previous-unrecovered": (
                "The previous service problem still needs repairing before another challenge "
                "can start."
            ),
            "attempt-busy": (
                "Another guide request is inspecting your service. Try again in a moment."
            ),
            "interrupted-attempt": (
                "The launch was interrupted. Check that your service works, then try "
                "`guide now` again. Ask for help if setup remains blocked; no challenge "
                "was credited."
            ),
            "injection-failed": (
                "I could not prepare the challenge safely. Check your site, then run "
                "`guide now` to retry; ask for help if setup keeps failing."
            ),
            "rollback-failed": (
                "The exercise could not recover safely. Your private backup is under "
                "~/.local/state/maker-guide/service-lab/. Ask for help; "
                "do not overwrite your unit blindly."
            ),
            "unit-changed": (
                "Your setup changed during preparation. Concurrent edits or rebuilt files "
                "were preserved, including in the private attempt directory. "
                "Ask for help before continuing."
            ),
        }.get(
            report.error,
            (
                "The local exercise could not finish safely. "
                "Check your service; ask for help if needed."
            ),
        )
    if not report.started:
        return "Run `guide now` to start this challenge before submitting a repair."
    if report.healthy:
        return (
            "Your service and local page work again. In one sentence, explain what caused "
            "the problem and why your repair worked: `guide answer 'your explanation'`."
        )
    return (
        prepared.launch_message + "\n\n" if prepared.launch_message else ""
    ) + "Find the cause and get your website working again. Ask me for a hint if you get stuck."
