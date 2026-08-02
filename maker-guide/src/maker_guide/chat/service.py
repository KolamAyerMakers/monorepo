"""Shared chat request handling."""

from __future__ import annotations

import sqlite3

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
from maker_guide.chat.snapshot import build_learner_snapshot
from maker_guide.chat.tutor import (
    append_response_draft_side_effects,
    calls_private_tutor,
)
from maker_guide.repositories.help_interaction import HelpInteraction, add_help_interaction
from maker_guide.repositories.helpers import transaction
from maker_guide.repositories.learner import Learner, get_learner


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
    prepared_answer_interpretation = prepare_answer_interpretation(
        request,
        dependencies,
        learner_handle,
    )
    with transaction(dependencies.database_connection):
        _require_learner(dependencies.database_connection, learner_handle)
        response_draft = build_response_draft(
            request,
            dependencies,
            learner_handle,
            interaction_timestamp,
            prepared_answer_interpretation,
        )
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
