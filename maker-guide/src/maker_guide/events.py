"""Event parsing, validation, redaction, and formatting."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, cast

MAX_IRC_MESSAGE_BYTES = 400
SECRET_PATTERNS = (
    re.compile(
        r"(?P<prefix>(?:password|passwd|token|secret|api[_-]?key)=)(?P<secret>\S+)",
        re.IGNORECASE,
    ),
    re.compile(r"(?P<prefix>Bearer\s+)(?P<secret>[A-Za-z0-9._~+/=-]+)", re.IGNORECASE),
)


class EventParseError(ValueError):
    """Raised when a socket payload cannot be accepted as an event."""


@dataclass(frozen=True, kw_only=True, slots=True)
class PeerCredentials:
    """Kernel-provided Unix socket peer identity."""

    process_id: int
    user_id: int
    group_id: int


@dataclass(frozen=True, kw_only=True, slots=True)
class ShellEvent:
    """Validated shell preexec event."""

    phase: Literal["before", "after"]
    user_id: int
    username: str
    process_id: int
    cwd: str
    command: str
    shell: str
    tty: str | None
    exit_status: int | None
    execute: bool
    timestamp: datetime
    ssh_auth_method: str | None = None
    """Authentication method read from sshd's SSH_USER_AUTH file."""
    event_id: str | None = None
    """Stable hook event identity, absent only for legacy clients."""


@dataclass(frozen=True, kw_only=True, slots=True)
class IrcOutboundMessage:
    """Message ready for IRC delivery."""

    channel: str
    text: str


def parse_shell_event(payload: bytes, credentials: PeerCredentials, username: str) -> ShellEvent:
    """Parse one JSON Lines payload into a shell event."""
    try:
        decoded = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise EventParseError("payload must be UTF-8") from error

    try:
        loaded = cast("object", json.loads(decoded))
    except json.JSONDecodeError as error:
        raise EventParseError("payload must be valid JSON") from error

    if not isinstance(loaded, dict):
        raise EventParseError("payload must be a JSON object")

    event_object = _string_key_mapping(cast("dict[object, object]", loaded))
    if event_object.get("version") != 1:
        raise EventParseError("version must be 1")
    phase = _event_phase(event_object.get("type"))

    return ShellEvent(
        event_id=_optional_event_id(event_object),
        phase=phase,
        user_id=credentials.user_id,
        username=username,
        process_id=credentials.process_id,
        cwd=_field_string(event_object, "cwd"),
        command=_field_string(event_object, "command"),
        shell=_optional_field_string(event_object, "shell", "bash"),
        tty=_optional_nullable_string(event_object, "tty"),
        exit_status=_exit_status(event_object, phase),
        execute=True,
        timestamp=_parse_timestamp(event_object.get("timestamp")),
        ssh_auth_method=_ssh_auth_method(event_object.get("ssh_auth_method")),
    )


def _optional_event_id(mapping: dict[str, object]) -> str | None:
    value = mapping.get("event_id")
    if value is None:
        return None
    if isinstance(value, str) and value:
        return value
    raise EventParseError("event_id must be a non-empty string")


def redact_command(command: str) -> str:
    """Redact common secret-looking command fragments."""
    redacted = command
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(r"\g<prefix>[redacted]", redacted)
    return redacted


def format_shell_event_for_irc(event: ShellEvent) -> str:
    """Format a shell event for channel output."""
    safe_command = _truncate_for_irc(_single_line(redact_command(event.command)))
    safe_cwd = _single_line(event.cwd)
    if event.phase == "after":
        return f"{event.username} after exit {event.exit_status} in {safe_cwd}: {safe_command}"
    return f"{event.username} before in {safe_cwd}: {safe_command}"


def _string_key_mapping(mapping: dict[object, object]) -> dict[str, object]:
    if all(isinstance(key, str) for key in mapping):
        return {key: value for key, value in mapping.items() if isinstance(key, str)}
    raise EventParseError("payload object keys must be strings")


def _field_string(mapping: dict[str, object], key: str) -> str:
    value = mapping.get(key)
    if isinstance(value, str) and value:
        return value
    raise EventParseError(f"{key} must be a non-empty string")


def _optional_field_string(mapping: dict[str, object], key: str, default: str) -> str:
    value = mapping.get(key, default)
    if isinstance(value, str) and value:
        return value
    raise EventParseError(f"{key} must be a non-empty string")


def _optional_nullable_string(mapping: dict[str, object], key: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if isinstance(value, str) and value:
        return value
    raise EventParseError(f"{key} must be null or a non-empty string")


def _event_phase(value: object) -> Literal["before", "after"]:
    if value == "preexec":
        return "before"
    if value == "postexec":
        return "after"
    raise EventParseError("type must be preexec or postexec")


def _ssh_auth_method(value: object) -> str | None:
    if value is None:
        return None
    if value in {"publickey", "password", "keyboard-interactive"}:
        return cast("str", value)
    raise EventParseError("ssh_auth_method is invalid")


def _exit_status(mapping: dict[str, object], phase: Literal["before", "after"]) -> int | None:
    value = mapping.get("exit_status")
    if phase == "before" and value is None:
        return None
    if phase == "after" and isinstance(value, int) and not isinstance(value, bool):
        return value
    if phase == "after":
        raise EventParseError("exit_status must be an integer for postexec")
    raise EventParseError("exit_status is only valid for postexec")


def _parse_timestamp(value: object) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if not isinstance(value, str) or not value:
        raise EventParseError("timestamp must be an ISO-8601 string")
    normalized = value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise EventParseError("timestamp must be a valid ISO-8601 string") from error
    if parsed.tzinfo is None:
        raise EventParseError("timestamp must include a timezone")
    return parsed.astimezone(UTC)


def _truncate_for_irc(text: str) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= MAX_IRC_MESSAGE_BYTES:
        return text
    shortened = encoded[: MAX_IRC_MESSAGE_BYTES - 3].decode("utf-8", errors="ignore")
    return f"{shortened}..."


def _single_line(text: str) -> str:
    return " ".join(text.splitlines())
