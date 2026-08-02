"""Chat request and response contracts."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from maker_guide.chat.snapshot import LearnerSnapshot
from maker_guide.curriculum.models import AnswerConceptAssessment, CourseCatalog
from maker_guide.llm_tutor import DEFAULT_TUTOR_MAX_TOKENS, AnswerInterpreter, TutorClient
from maker_guide.validation_paths import UnixAccountLookup, lookup_unix_account

ChatVisibility = Literal["public", "private"]
DEFAULT_CHAT_MAX_INPUT_CHARS = 16_384
CHAT_INPUT_TOO_LONG_TEXT = (
    f"Your message is too long. Keep help requests under {DEFAULT_CHAT_MAX_INPUT_CHARS} characters."
)


@dataclass(frozen=True, kw_only=True, slots=True)
class CliChatContext:
    """CLI-specific chat context."""

    username: str
    """Unix username that maps directly to the learner handle."""
    terminal: str | None
    """Terminal device path, if known."""
    ssh_connection: str | None = None
    """SSH_CONNECTION value when the CLI is running inside SSH."""
    source: Literal["cli"] = "cli"
    """Source label stored in help interactions."""


@dataclass(frozen=True, kw_only=True, slots=True)
class IrcChatContext:
    """IRC-specific chat context."""

    nickname: str
    """IRC nickname that maps directly to the learner handle."""
    target: str
    """IRC PRIVMSG target."""
    reply_target: str
    """IRC target where the bot should respond."""
    source: Literal["irc"] = "irc"
    """Source label stored in help interactions."""


type ChatContext = CliChatContext | IrcChatContext


@dataclass(frozen=True, kw_only=True, slots=True)
class ChatRequest:
    """One user message with transport metadata."""

    context: ChatContext
    """Transport-specific message context."""
    visibility: ChatVisibility
    """Whether the request came from public or private chat."""
    text: str
    """Message text after transport-specific command gating."""


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass(frozen=True, kw_only=True, slots=True)
class ChatDependencies:
    """Dependencies required by shared chat handling."""

    database_connection: sqlite3.Connection
    """SQLite connection for learner state and help interaction writes."""
    catalog: CourseCatalog
    """Course catalog used to build deterministic learner snapshots."""
    bot_name: str
    """Configured bot name visible to learners."""
    tutor_client: TutorClient | None = None
    """Optional read-only LLM tutor for private fallback help."""
    answer_interpreter: AnswerInterpreter | None = None
    """Optional read-only semantic interpreter for private learner answers."""
    tutor_max_tokens: int = DEFAULT_TUTOR_MAX_TOKENS
    """Maximum tokens to request from the tutor provider."""
    timestamp_factory: Callable[[], str] = _utc_timestamp
    """Factory for audit-friendly interaction timestamps."""
    account_lookup: UnixAccountLookup = lookup_unix_account
    """Unix account lookup used by filesystem validation rules."""
    response_chunk_writer: Callable[[str], None] | None = None
    """Optional learner-facing stream sink for private tutor chunks."""


@dataclass(frozen=True, kw_only=True, slots=True)
class ChatResponse:
    """Bot response to one chat request."""

    text: str
    """Response text to send to the learner."""
    learner_snapshot: LearnerSnapshot
    """Snapshot used to handle the request."""
    retry_after_irc_client_verification: bool = False
    """Whether IRC should request client evidence and retry the original request."""
    public_announcements: tuple[str, ...] = ()
    """Promotion notices for IRC public channels."""


@dataclass(frozen=True, kw_only=True, slots=True)
class ResponseDraft:
    """Internal response text plus help-interaction metadata."""

    text: str
    """Response text to send."""
    topic_tags: tuple[str, ...]
    """Topic tags to store with the help interaction."""
    restricted_llm_audit_log: RestrictedLlmAuditLogInput | None = None
    """Restricted LLM audit log to persist with the chat response."""
    tutor_audit_event: TutorAuditEvent | None = None
    """Tutor audit event to persist with the chat response."""
    retry_after_irc_client_verification: bool = False
    """Whether IRC should request client evidence and retry the original request."""
    public_announcements: tuple[str, ...] = ()
    """Promotion notices for IRC public channels."""


@dataclass(frozen=True, kw_only=True, slots=True)
class PreparedAnswerInterpretation:
    """Provider analysis prepared before the progress transaction starts."""

    target_type: Literal["quest", "session_objective"]
    target_id: str
    target_session_id: str | None
    assessments: tuple[AnswerConceptAssessment, ...]
    feedback: str | None
    restricted_llm_audit_log: RestrictedLlmAuditLogInput


@dataclass(frozen=True, kw_only=True, slots=True)
class TutorAuditEvent:
    """Audit event data for tutor usage."""

    learner_handle: str
    """Learner handle for the audit row."""
    source: str
    """Chat source that requested the tutor."""
    timestamp: str
    """Audit event timestamp."""
    event_type: str
    """Audit event type."""
    payload: dict[str, object]
    """Audit event payload."""


@dataclass(frozen=True, kw_only=True, slots=True)
class RestrictedLlmAuditLogInput:
    """Restricted full LLM audit payload data."""

    provider: str
    """LLM provider id, or unavailable when no provider response was reached."""
    model: str
    """LLM model id, or unavailable when no provider response was reached."""
    status: str
    """Interaction status, such as answered, failed, or rate_limited."""
    request_payload: dict[str, object]
    """Full provider request payload, without API credentials."""
    response_payload: dict[str, object]
    """Full provider response payload or structured failure details."""


class ChatError(RuntimeError):
    """Raised when chat handling preconditions are not met."""


class UnknownLearnerError(ChatError):
    """Raised when a chat request comes from an unknown learner handle."""
