"""Tests for narrow Unix group helpers."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence

import pytest

from maker_guide.unix_group_helpers import (
    SystemCommandRunner,
    UnixGroupHelperError,
    run_grant_group_helper,
    run_revoke_group_helper,
)


def test_grant_group_helper_uses_fixed_usermod_command() -> None:
    """Grant helper validates names and delegates to fixed usermod arguments."""
    commands: list[tuple[str, ...]] = []

    assert (
        run_grant_group_helper(
            ("alice", "makers"),
            _record_command(commands),
            frozenset({"makers"}),
        )
        == 0
    )
    assert commands == [("/usr/sbin/usermod", "-a", "-G", "makers", "alice")]


def test_revoke_group_helper_uses_fixed_gpasswd_command() -> None:
    """Revoke helper validates names and delegates to fixed gpasswd arguments."""
    commands: list[tuple[str, ...]] = []

    assert (
        run_revoke_group_helper(
            ("alice", "makers"),
            _record_command(commands),
            frozenset({"makers"}),
        )
        == 0
    )
    assert commands == [("/usr/bin/gpasswd", "-d", "alice", "makers")]


def test_group_helper_rejects_unsafe_names() -> None:
    """Unsafe helper arguments are rejected before subprocess execution."""
    commands: list[tuple[str, ...]] = []

    with pytest.raises(UnixGroupHelperError, match="handle must be a safe Unix name"):
        run_grant_group_helper(
            ("bad handle", "makers"),
            _record_command(commands),
            frozenset({"makers"}),
        )

    assert commands == []


def test_group_helper_requires_managed_groups() -> None:
    """Helpers fail closed when no root-side allowlist is available."""
    commands: list[tuple[str, ...]] = []

    with pytest.raises(UnixGroupHelperError, match="managed groups are required"):
        run_grant_group_helper(("alice", "makers"), _record_command(commands))

    assert commands == []


def test_group_helper_rejects_unmanaged_group() -> None:
    """Helpers reject safe but unmanaged group names before subprocess execution."""
    commands: list[tuple[str, ...]] = []

    with pytest.raises(UnixGroupHelperError, match="unmanaged group: sudo"):
        run_grant_group_helper(
            ("alice", "sudo"),
            _record_command(commands),
            frozenset({"makers"}),
        )

    assert commands == []


def test_group_helper_system_command_uses_bounded_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Privileged helper subprocesses receive a bounded timeout."""
    recorded_timeout: list[float | None] = []

    def run_with_timeout(
        arguments: list[str],
        *,
        check: bool,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        assert check is False
        recorded_timeout.append(timeout)
        raise subprocess.TimeoutExpired(arguments, timeout)

    monkeypatch.setattr(subprocess, "run", run_with_timeout)

    with pytest.raises(subprocess.TimeoutExpired):
        run_revoke_group_helper(("alice", "makers"), managed_groups=frozenset({"makers"}))

    assert recorded_timeout == [10.0]


def _record_command(commands: list[tuple[str, ...]]) -> SystemCommandRunner:
    def command_runner(arguments: Sequence[str]) -> int:
        commands.append(tuple(arguments))
        return 0

    return command_runner
