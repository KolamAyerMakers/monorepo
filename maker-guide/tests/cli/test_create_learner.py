"""Tests for the Maker Guide learner creation wrapper."""

from __future__ import annotations

import io
import pwd
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

from maker_guide.cli import create_learner
from maker_guide.deployment import (
    CONFIGURATION_FILE,
    LLDAP_CREATE_USER_COMMAND,
    MAKER_GUIDE_DAEMON_USER,
    MAKER_GUIDE_INITIALIZE_LEARNER_COMMAND,
    REFRESH_LEARNER_ROUTES_COMMAND,
    RUN_USER_COMMAND,
)


def test_main_creates_lldap_user_then_initializes_learner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The wrapper keeps LLDAP generic and performs app initialization separately."""
    commands: list[Sequence[str]] = []

    def run(
        command: Sequence[str],
        **keyword_arguments: object,
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        assert keyword_arguments["check"] is True
        return subprocess.CompletedProcess(command, 0, stdout="20001\n")

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(sys, "stdin", io.StringIO("private comet window river signal\n"))
    monkeypatch.setattr(create_learner, "registration_is_open", _registration_is_open)
    monkeypatch.setattr(pwd, "getpwnam", _missing_account)

    assert (
        create_learner.main(
            [
                "--registration-mode",
                "alice",
                "--email",
                "alice@kolamayermakers.org",
                "--password-stdin",
            ]
        )
        == 0
    )
    assert commands == [
        [
            LLDAP_CREATE_USER_COMMAND,
            "alice",
            "--email",
            "alice@kolamayermakers.org",
            "--print-user-id-number",
            "--password-stdin",
        ],
        [
            RUN_USER_COMMAND,
            "-u",
            MAKER_GUIDE_DAEMON_USER,
            "--",
            MAKER_GUIDE_INITIALIZE_LEARNER_COMMAND,
            "alice",
            "--uid",
            "20001",
            "--config",
            CONFIGURATION_FILE,
        ],
        [REFRESH_LEARNER_ROUTES_COMMAND],
    ]


def test_main_returns_nonzero_when_lldap_helper_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Subprocess failures are reported without running later steps."""

    def run(
        command: Sequence[str],
        **keyword_arguments: object,
    ) -> subprocess.CompletedProcess[str]:
        assert keyword_arguments["check"] is True
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(sys, "stdin", io.StringIO("private comet window river signal\n"))
    monkeypatch.setattr(create_learner, "registration_is_open", _registration_is_open)

    assert (
        create_learner.main(
            [
                "--registration-mode",
                "alice",
                "--email",
                "alice@kolamayermakers.org",
                "--password-stdin",
            ]
        )
        == 1
    )
    assert f"{LLDAP_CREATE_USER_COMMAND} alice" in capsys.readouterr().err


def test_resume_skips_lldap_and_retries_remaining_provisioning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Recovery does not try to recreate an account that already exists."""
    commands: list[Sequence[str]] = []

    def run(
        command: Sequence[str],
        **_keyword_arguments: object,
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="20001\n")

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(pwd, "getpwnam", _getpwnam)

    assert create_learner.main(["--resume", "alice"]) == 0
    assert commands == [
        [
            RUN_USER_COMMAND,
            "-u",
            MAKER_GUIDE_DAEMON_USER,
            "--",
            MAKER_GUIDE_INITIALIZE_LEARNER_COMMAND,
            "alice",
            "--uid",
            "20001",
            "--config",
            CONFIGURATION_FILE,
        ],
        [REFRESH_LEARNER_ROUTES_COMMAND],
    ]


def test_resume_rejects_missing_posix_account(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Recovery cannot initialize a username that provisioning never created."""

    def missing_account(_username: str) -> pwd.struct_passwd:
        raise KeyError

    monkeypatch.setattr(pwd, "getpwnam", missing_account)

    assert create_learner.main(["--resume", "alice"]) == 1
    assert capsys.readouterr().err == "Cannot resume: the POSIX account does not exist.\n"


def test_main_reports_resume_command_after_post_creation_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A created account has an explicit safe recovery path after initialization fails."""
    calls = 0

    def run(
        command: Sequence[str],
        **_keyword_arguments: object,
    ) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 0, stdout="20001\n")

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(sys, "stdin", io.StringIO("private comet window river signal\n"))
    monkeypatch.setattr(create_learner, "registration_is_open", _registration_is_open)
    monkeypatch.setattr(pwd, "getpwnam", _getpwnam)

    assert (
        create_learner.main(
            [
                "--registration-mode",
                "alice",
                "--email",
                "alice@kolamayermakers.org",
                "--password-stdin",
            ],
        )
        == 1
    )
    assert "Account created but Maker Guide provisioning is incomplete." in capsys.readouterr().err


def test_main_rejects_registration_when_closed(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Registration mode requires the root-owned open marker."""

    def registration_is_closed(_state_file: Path) -> bool:
        return False

    monkeypatch.setattr(create_learner, "registration_is_open", registration_is_closed)
    monkeypatch.setattr(sys, "stdin", io.StringIO("private comet window river signal\n"))
    assert (
        create_learner.main(
            [
                "--registration-mode",
                "alice",
                "--email",
                "alice@kolamayermakers.org",
                "--password-stdin",
            ]
        )
        == 1
    )
    assert capsys.readouterr().err == "Registration is closed.\n"


def test_registration_mode_rejects_privileged_command_overrides() -> None:
    """Registration callers cannot override root helper commands."""
    with pytest.raises(SystemExit):
        create_learner.parse_arguments(
            [
                "--registration-mode",
                "alice",
                "--email",
                "alice@kolamayermakers.org",
                "--password-stdin",
                "--run-user",
                "root",
            ],
        )


def _registration_is_open(_state_file: Path) -> bool:
    return True


def _getpwnam(_username: str) -> pwd.struct_passwd:
    return pwd.struct_passwd(("alice", "x", 20001, 20001, "", "/home/alice", "/bin/bash"))


def _missing_account(_username: str) -> pwd.struct_passwd:
    raise KeyError
