"""Tests for shell event parsing and formatting."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from maker_guide.events import (
    EventParseError,
    PeerCredentials,
    ShellEvent,
    format_shell_event_for_irc,
    parse_shell_event,
    redact_command,
)


def test_parse_shell_event_uses_peer_identity() -> None:
    """The daemon must not trust UID or username values from the JSON payload."""
    payload = json.dumps(
        {
            "version": 1,
            "type": "preexec",
            "uid": 9999,
            "username": "mallory",
            "cwd": "/repo",
            "command": "git status",
            "shell": "bash",
            "tty": "/dev/pts/3",
            "timestamp": "2026-05-24T12:34:56Z",
        },
    ).encode("utf-8")

    event = parse_shell_event(
        payload,
        PeerCredentials(process_id=1234, user_id=1001, group_id=1001),
        "alice",
    )

    fixed_timestamp = datetime(2026, 5, 24, 12, 34, 56, tzinfo=UTC)
    assert replace(event, timestamp=fixed_timestamp) == ShellEvent(
        user_id=1001,
        username="alice",
        process_id=1234,
        phase="before",
        cwd="/repo",
        command="git status",
        shell="bash",
        tty="/dev/pts/3",
        exit_status=None,
        execute=True,
        timestamp=fixed_timestamp,
    )


@pytest.mark.parametrize(
    "payload",
    [
        b"not-json",
        b"[]",
        b'{"version":2,"type":"preexec"}',
        b'{"version":1,"type":"other"}',
        b'{"version":1,"type":"preexec","cwd":"/repo"}',
    ],
)
def test_parse_shell_event_rejects_invalid_payloads(payload: bytes) -> None:
    """Malformed or incomplete socket input is rejected."""
    with pytest.raises(EventParseError):
        parse_shell_event(
            payload,
            PeerCredentials(process_id=1234, user_id=1001, group_id=1001),
            "alice",
        )


def test_redact_command_removes_common_secrets() -> None:
    """Common secret formats are redacted before IRC formatting."""
    assert redact_command("deploy token=abc123 Authorization: Bearer xyz") == (
        "deploy token=[redacted] Authorization: Bearer [redacted]"
    )


def test_format_shell_event_for_irc_includes_user_directory_and_command() -> None:
    """IRC output includes useful context with secrets removed."""
    event = parse_shell_event(
        b'{"version":1,"type":"preexec","cwd":"/repo","command":"make token=abc"}',
        PeerCredentials(process_id=1234, user_id=1001, group_id=1001),
        "alice",
    )

    assert format_shell_event_for_irc(event) == "alice before in /repo: make token=[redacted]"


def test_parse_postexec_event_requires_exit_status() -> None:
    """Postexec events include the command exit status."""
    event = parse_shell_event(
        b'{"version":1,"type":"postexec","cwd":"/repo","command":"make","exit_status":2}',
        PeerCredentials(process_id=1234, user_id=1001, group_id=1001),
        "alice",
    )

    fixed_timestamp = event.timestamp
    assert replace(event, timestamp=fixed_timestamp) == ShellEvent(
        user_id=1001,
        username="alice",
        process_id=1234,
        phase="after",
        cwd="/repo",
        command="make",
        shell="bash",
        tty=None,
        exit_status=2,
        execute=True,
        timestamp=fixed_timestamp,
    )
    assert format_shell_event_for_irc(event) == "alice after exit 2 in /repo: make"


def test_format_shell_event_for_irc_removes_protocol_line_breaks() -> None:
    """IRC output cannot contain CRLF protocol injection from local event fields."""
    event = parse_shell_event(
        json.dumps(
            {
                "version": 1,
                "type": "preexec",
                "cwd": "/repo\r\nPRIVMSG #ops :owned",
                "command": "printf hello\nJOIN #ops",
            },
        ).encode("utf-8"),
        PeerCredentials(process_id=1234, user_id=1001, group_id=1001),
        "alice",
    )

    formatted = format_shell_event_for_irc(event)

    assert formatted == "alice before in /repo PRIVMSG #ops :owned: printf hello JOIN #ops"
