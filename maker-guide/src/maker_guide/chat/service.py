"""Shared chat request handling."""

from __future__ import annotations

import secrets
import sqlite3
from dataclasses import replace

from maker_guide.chat.answer_interpretation import prepare_answer_interpretation
from maker_guide.chat.contract import (
    CHAT_INPUT_TOO_LONG_TEXT,
    DEFAULT_CHAT_MAX_INPUT_CHARS,
    ChatContext,
    ChatDependencies,
    ChatRequest,
    ChatResponse,
    CliChatContext,
    IrcChatContext,
    ResponseDraft,
    UnknownLearnerError,
)
from maker_guide.chat.router import build_response_draft
from maker_guide.chat.service_lab import current_lab_report, lab_status_text, prepare_service_lab
from maker_guide.chat.site_check import prepare_site_check
from maker_guide.chat.snapshot import build_learner_snapshot
from maker_guide.chat.tutor import (
    append_response_draft_side_effects,
    calls_private_tutor,
)
from maker_guide.repositories.help_interaction import HelpInteraction, add_help_interaction
from maker_guide.repositories.helpers import transaction
from maker_guide.repositories.learner import Learner, get_learner
from maker_guide.repositories.session_objective_completion import list_completed_objective_ids


def handle_chat_request(request: ChatRequest, dependencies: ChatDependencies) -> ChatResponse:
    """Return a response for a user chat request and record the interaction."""
    learner_handle = _learner_handle_from_context(request.context)
    interaction_timestamp = dependencies.timestamp_factory()

    if len(request.text) > DEFAULT_CHAT_MAX_INPUT_CHARS:
        with transaction(dependencies.database_connection):
            _require_learner(dependencies.database_connection, learner_handle)
            return ChatResponse(
                text=CHAT_INPUT_TOO_LONG_TEXT,
                learner_snapshot=build_learner_snapshot(
                    dependencies.database_connection,
                    dependencies.catalog,
                    learner_handle,
                ),
            )

    _require_learner(dependencies.database_connection, learner_handle)
    dependencies = replace(
        dependencies,
        service_lab_result=prepare_service_lab(
            request, dependencies, learner_handle, interaction_timestamp
        ),
    )
    if calls_private_tutor(request, dependencies, learner_handle):
        _require_learner(dependencies.database_connection, learner_handle)
        response_draft = build_response_draft(
            request,
            dependencies,
            learner_handle,
            interaction_timestamp,
        )
        with transaction(dependencies.database_connection):
            _require_learner(dependencies.database_connection, learner_handle)
            return _record_chat_response(
                request,
                dependencies,
                learner_handle,
                interaction_timestamp,
                response_draft,
            )

    _require_learner(dependencies.database_connection, learner_handle)
    dependencies = replace(
        dependencies,
        site_check_result=(
            prepare_site_check(request, dependencies, learner_handle)
            if dependencies.service_lab_result is None
            else None
        ),
    )
    prepared_answer_interpretation = prepare_answer_interpretation(
        request,
        dependencies,
        learner_handle,
    )
    with transaction(dependencies.database_connection):
        _require_learner(dependencies.database_connection, learner_handle)
        lab_report = current_lab_report(dependencies, learner_handle)
        response_draft = build_response_draft(
            request,
            dependencies,
            learner_handle,
            interaction_timestamp,
            prepared_answer_interpretation,
        )
        completed_lab = (
            dependencies.service_lab_result is not None
            and lab_report is not None
            and lab_report.healthy
            and dependencies.service_lab_result.objective_id
            in list_completed_objective_ids(
                dependencies.database_connection,
                learner_handle,
                dependencies.service_lab_result.course_id,
                dependencies.service_lab_result.session_id,
            )
        )
        if not completed_lab:
            return _record_chat_response(
                request,
                dependencies,
                learner_handle,
                interaction_timestamp,
                response_draft,
            )
    if completed_lab:
        # Commit the repair before asking the learner-side runner to break the next lab.
        next_lab = prepare_service_lab(
            replace(request, text="now"), dependencies, learner_handle, interaction_timestamp
        )
        congratulations, transition = secrets.choice(
            (
                (
                    "You got it working again! Great detective work.",
                    (
                        "So, I tried to help with something else... and broke your website again. "
                        "Sorry. Can you take another look?"
                    ),
                ),
                (
                    "That's it! Fixed and explained. Nicely done!",
                    (
                        "I should have left it there. Instead, I made one more change... "
                        "and now your website needs rescuing again. My fault."
                    ),
                ),
                (
                    "The site is back! You nailed that repair.",
                    (
                        "That was my cue to stop touching things. I did not take the hint. "
                        "Sorry... there's a new problem to investigate."
                    ),
                ),
            )
        )
        response_draft = replace(
            response_draft,
            text=congratulations
            + "\n\n"
            + (
                lab_status_text(
                    replace(next_lab, launch_message=transition)
                    if next_lab.launch_message is not None
                    else next_lab
                )
                if next_lab is not None
                else response_draft.text.partition("\n\n")[2]
            ),
        )
    with transaction(dependencies.database_connection):
        return _record_chat_response(
            request,
            dependencies,
            learner_handle,
            interaction_timestamp,
            response_draft,
        )


def _record_chat_response(
    request: ChatRequest,
    dependencies: ChatDependencies,
    learner_handle: str,
    interaction_timestamp: str,
    response_draft: ResponseDraft,
) -> ChatResponse:
    learner_snapshot = build_learner_snapshot(
        dependencies.database_connection,
        dependencies.catalog,
        learner_handle,
    )
    response = ChatResponse(
        text=response_draft.text,
        learner_snapshot=learner_snapshot,
        retry_after_irc_client_verification=response_draft.retry_after_irc_client_verification,
        public_announcements=response_draft.public_announcements,
    )
    append_response_draft_side_effects(
        dependencies,
        learner_handle,
        request.context.source,
        interaction_timestamp,
        response_draft,
    )
    add_help_interaction(
        dependencies.database_connection,
        HelpInteraction(
            id=None,
            handle=learner_handle,
            source=request.context.source,
            visibility=request.visibility,
            question=request.text,
            response=response.text,
            topic_tags=response_draft.topic_tags,
            created_at=interaction_timestamp,
            answered_at=interaction_timestamp,
        ),
    )
    return response


def _learner_handle_from_context(context: ChatContext) -> str:
    match context:
        case CliChatContext(username=username):
            return username
        case IrcChatContext(nickname=nickname):
            return nickname


def _require_learner(database_connection: sqlite3.Connection, handle: str) -> Learner:
    learner = get_learner(database_connection, handle)
    if learner is None:
        raise UnknownLearnerError(f"unknown learner handle: {handle}")
    return learner
