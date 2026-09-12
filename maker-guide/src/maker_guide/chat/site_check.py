"""Prepare one authenticated local site check without holding a database transaction."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import cast

from maker_guide.chat.contract import (
    ChatDependencies,
    ChatRequest,
    CliChatContext,
    PreparedSiteCheck,
)
from maker_guide.chat.intents import chat_intent
from maker_guide.chat.snapshot import build_learner_snapshot
from maker_guide.curriculum.models import SiteCheckValidation
from maker_guide.progress.models import ProgressServiceError
from maker_guide.progress.service import current_session_objective
from maker_guide.repositories.quest_assignment import get_assignment
from maker_guide.site_check import SiteCheckError, SiteCheckReport, read_site_check_source


def prepare_site_check(  # noqa: C901, PLR0911 - Reject ineligible tasks before any local execution.
    request: ChatRequest,
    dependencies: ChatDependencies,
    learner_handle: str,
) -> PreparedSiteCheck | None:
    """Select read-only, hash the fixed source, then ask only the capable CLI to run it."""
    if (
        not isinstance(request.context, CliChatContext)
        or request.visibility != "private"
        or chat_intent(request.text) not in {"now", "check"}
        or dependencies.site_check_runner is None
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
        return None
    if objective_result.objective is not None:
        if not isinstance(objective_result.objective.validation, SiteCheckValidation):
            return None
        prepared = PreparedSiteCheck(
            course_id=dependencies.catalog.course.id,
            target_type="session_objective",
            target_id=objective_result.objective.id,
            target_session_id=objective_result.session_id,
            evidence_since=objective_result.evidence_since,
            report=None,
        )
    else:
        snapshot = build_learner_snapshot(
            dependencies.database_connection, dependencies.catalog, learner_handle
        )
        if not snapshot.pending_quests:
            return None
        quest = dependencies.catalog.quest(snapshot.pending_quests[0])
        if not isinstance(quest.validation, SiteCheckValidation):
            return None
        assignment = get_assignment(
            dependencies.database_connection,
            learner_handle,
            dependencies.catalog.course.id,
            quest.id,
        )
        if assignment is None:
            return None
        prepared = PreparedSiteCheck(
            course_id=dependencies.catalog.course.id,
            target_type="quest",
            target_id=quest.id,
            target_session_id=None,
            evidence_since=assignment.assigned_at,
            report=None,
        )
    try:
        source_sha256 = hashlib.sha256(
            read_site_check_source(learner_handle, account_lookup=dependencies.account_lookup)
        ).hexdigest()
    except SiteCheckError as error:
        return replace(prepared, failure_reason=str(error))
    try:
        report = cast("object", dependencies.site_check_runner(source_sha256))
    except (OSError, EOFError, ValueError):
        return replace(prepared, failure_reason="site-check-failed")
    if not isinstance(report, SiteCheckReport):
        return replace(prepared, failure_reason="site-check-failed")
    if report.source_sha256 != source_sha256:
        return replace(prepared, failure_reason="site-check-stale")
    return replace(prepared, report=report)
