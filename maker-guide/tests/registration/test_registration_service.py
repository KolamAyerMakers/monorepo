"""Tests for learner registration workflow."""

from __future__ import annotations

import io
import logging
import subprocess
from collections.abc import Sequence
from typing import TYPE_CHECKING

from rich.console import Console

from maker_guide.deployment import MAKER_GUIDE_CREATE_LEARNER_COMMAND
from maker_guide.registration.models import RegistrationOptions, RegistrationRequest
from maker_guide.registration.service import (
    RegistrationRuntime,
    create_user_command,
    is_username_available,
    passphrase_strength_error,
    print_success_message,
    run_main_loop,
)

if TYPE_CHECKING:
    import pytest


def _options() -> RegistrationOptions:
    return RegistrationOptions(
        create_user_command=MAKER_GUIDE_CREATE_LEARNER_COMMAND,
        sudo_command="/usr/bin/sudo",
        getent_command="/usr/bin/getent",
        pwscore_command="/usr/bin/pwscore",
        logo_command="/missing-logo",
        fully_qualified_domain_name="classroom.example",
        login_host="classroom.example",
        web_ssh_url="https://ssh.example",
    )


class _PromptInput:
    def __init__(self, values: Sequence[str]) -> None:
        self._values = list(values)
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self._values:
            raise AssertionError("unexpected prompt")
        return self._values.pop(0)


class _SecretInput:
    def __init__(self, values: Sequence[str]) -> None:
        self._values = list(values)
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self._values:
            raise AssertionError("unexpected secret prompt")
        return self._values.pop(0)


def _runtime(
    prompt_values: Sequence[str],
    secret_values: Sequence[str],
    environment: dict[str, str] | None = None,
) -> tuple[RegistrationRuntime, io.StringIO]:
    output_stream = io.StringIO()
    return (
        RegistrationRuntime(
            options=_options(),
            console=Console(file=output_stream, color_system=None, width=120),
            input_line=_PromptInput(prompt_values),
            input_secret=_SecretInput(secret_values),
            environment=environment or {},
        ),
        output_stream,
    )


def test_create_user_command_uses_supplied_email() -> None:
    """The create-user command forwards an explicitly supplied email."""
    assert create_user_command(
        _options(),
        RegistrationRequest(
            username="alice",
            email="alice@example.test",
            passphrase="secret phrase",
        ),
    ) == [
        "/usr/bin/sudo",
        "-n",
        MAKER_GUIDE_CREATE_LEARNER_COMMAND,
        "--registration-mode",
        "alice",
        "--email",
        "alice@example.test",
        "--password-stdin",
    ]


def test_create_user_command_uses_default_email_domain() -> None:
    """The create-user command derives email when the learner skips email."""
    assert (
        create_user_command(
            _options(),
            RegistrationRequest(username="alice", email=None, passphrase="secret phrase"),
        )[6]
        == "alice@classroom.example"
    )


def test_is_username_available_returns_false_when_getent_finds_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A local passwd hit means the learner username is unavailable."""

    def fake_run(
        command: Sequence[str],
        **keyword_arguments: object,
    ) -> subprocess.CompletedProcess[str]:
        assert command == ["getent", "passwd", "alice"]
        assert keyword_arguments["check"] is False
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert not is_username_available("getent", "alice")


def test_is_username_available_returns_true_when_getent_misses_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A local passwd miss means the learner username is available."""

    def fake_run(
        command: Sequence[str],
        **keyword_arguments: object,
    ) -> subprocess.CompletedProcess[str]:
        assert keyword_arguments["check"] is False
        return subprocess.CompletedProcess(command, 2)

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert is_username_available("getent", "alice")


def test_passphrase_strength_uses_pwscore(monkeypatch: pytest.MonkeyPatch) -> None:
    """System passphrase policy is checked with the configured pwscore command."""

    def fake_run(
        command: Sequence[str],
        **keyword_arguments: object,
    ) -> subprocess.CompletedProcess[str]:
        assert command == ["pwscore"]
        assert keyword_arguments["input"] == "private comet window river signal\n"
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert (
        passphrase_strength_error("pwscore", "alice", "private comet window river signal") is None
    )


def test_success_message_mentions_ssh_for_terminal_registration() -> None:
    """Terminal registration tells learners how to connect with SSH."""
    registration_runtime, output_stream = _runtime([], [])

    print_success_message(registration_runtime, "alice")

    assert "ssh alice@classroom.example" in output_stream.getvalue()


def test_success_message_mentions_web_ssh_when_configured() -> None:
    """Registration points learners to web SSH when configured."""
    registration_runtime, output_stream = _runtime([], [])

    print_success_message(registration_runtime, "alice")

    assert "https://ssh.example" in output_stream.getvalue()
    assert "sign in as 'alice'" in output_stream.getvalue()


def test_main_loop_registers_user(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The main loop collects inputs and invokes the privileged user helper."""
    commands: list[Sequence[str]] = []

    def fake_run(
        command: Sequence[str],
        **keyword_arguments: object,
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if command == ["/missing-logo"]:
            raise FileNotFoundError
        if command == ["/usr/bin/getent", "passwd", "alice"]:
            return subprocess.CompletedProcess(command, 2)
        if command == ["/usr/bin/pwscore"]:
            assert keyword_arguments["input"] == "private comet window river signal\n"
            return subprocess.CompletedProcess(command, 0)
        assert command == [
            "/usr/bin/sudo",
            "-n",
            MAKER_GUIDE_CREATE_LEARNER_COMMAND,
            "--registration-mode",
            "alice",
            "--email",
            "alice@classroom.example",
            "--password-stdin",
        ]
        assert keyword_arguments["input"] == "private comet window river signal\n"
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    registration_runtime, output_stream = _runtime(
        ["", "alice", ""],
        ["private comet window river signal", "private comet window river signal"],
    )

    with caplog.at_level(logging.INFO, logger="maker_guide.registration.service"):
        assert run_main_loop(registration_runtime) == 0
    assert "Registration successful." in output_stream.getvalue()
    assert "Registration completed for username alice." in caplog.messages
    assert commands[-1][0:3] == [
        "/usr/bin/sudo",
        "-n",
        MAKER_GUIDE_CREATE_LEARNER_COMMAND,
    ]


def test_main_loop_retries_when_username_is_taken(monkeypatch: pytest.MonkeyPatch) -> None:
    """A taken username sends the learner back to the username prompt."""

    def fake_run(
        command: Sequence[str],
        **keyword_arguments: object,
    ) -> subprocess.CompletedProcess[str]:
        assert keyword_arguments["check"] is False
        if command == ["/missing-logo"]:
            raise FileNotFoundError
        if command == ["/usr/bin/getent", "passwd", "alice"]:
            return subprocess.CompletedProcess(command, 0)
        if command == ["/usr/bin/getent", "passwd", "bob"]:
            return subprocess.CompletedProcess(command, 2)
        if command == ["/usr/bin/pwscore"]:
            return subprocess.CompletedProcess(command, 0)
        assert command[4] == "bob"
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    registration_runtime, output_stream = _runtime(
        ["", "alice", "bob", ""],
        ["private comet window river signal", "private comet window river signal"],
    )

    assert run_main_loop(registration_runtime) == 0
    assert "Taken: alice. Try another one." in output_stream.getvalue()


def test_main_loop_retries_when_passphrase_is_weak(monkeypatch: pytest.MonkeyPatch) -> None:
    """A weak system-policy passphrase sends the learner back to the prompt."""

    def fake_run(
        command: Sequence[str],
        **keyword_arguments: object,
    ) -> subprocess.CompletedProcess[str]:
        if command == ["/missing-logo"]:
            raise FileNotFoundError
        if command == ["/usr/bin/getent", "passwd", "alice"]:
            return subprocess.CompletedProcess(command, 2)
        if command == ["/usr/bin/pwscore"]:
            if keyword_arguments["input"] == "correct horse battery staple\n":
                return subprocess.CompletedProcess(command, 1, stderr="too short")
            return subprocess.CompletedProcess(command, 0)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    registration_runtime, output_stream = _runtime(
        ["", "alice", ""],
        [
            "correct horse battery staple",
            "private comet window river signal",
            "private comet window river signal",
        ],
    )

    assert run_main_loop(registration_runtime) == 0
    assert "Not strong enough: too short" in output_stream.getvalue()


def test_main_loop_retries_when_passphrases_do_not_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A confirmation mismatch sends the learner back to the passphrase prompt."""

    def fake_run(
        command: Sequence[str],
        **keyword_arguments: object,
    ) -> subprocess.CompletedProcess[str]:
        assert keyword_arguments["check"] is False
        if command == ["/missing-logo"]:
            raise FileNotFoundError
        if command == ["/usr/bin/getent", "passwd", "alice"]:
            return subprocess.CompletedProcess(command, 2)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    registration_runtime, output_stream = _runtime(
        ["", "alice", ""],
        [
            "private comet window river signal",
            "different private phrase",
            "private comet window river signal",
            "private comet window river signal",
        ],
    )

    assert run_main_loop(registration_runtime) == 0
    assert "Those did not match. Re-enter the passphrase." in output_stream.getvalue()


def test_main_loop_returns_nonzero_when_account_creation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed privileged helper call shows its error and exits nonzero."""

    def fake_run(
        command: Sequence[str],
        **keyword_arguments: object,
    ) -> subprocess.CompletedProcess[str]:
        assert keyword_arguments["check"] is False
        if command == ["/missing-logo"]:
            raise FileNotFoundError
        if command == ["/usr/bin/getent", "passwd", "alice"]:
            return subprocess.CompletedProcess(command, 2)
        if command == ["/usr/bin/pwscore"]:
            return subprocess.CompletedProcess(command, 0)
        return subprocess.CompletedProcess(command, 1, stderr="lldap rejected user")

    monkeypatch.setattr(subprocess, "run", fake_run)
    registration_runtime, output_stream = _runtime(
        ["", "alice", "q"],
        ["private comet window river signal", "private comet window river signal"],
    )

    assert run_main_loop(registration_runtime) == 1
    assert "Account creation failed: lldap rejected user" in output_stream.getvalue()


def test_main_loop_returns_cancelled_status() -> None:
    """Cancelling learner input exits with the conventional interrupted status."""

    def cancelled_input(ignored_prompt: str) -> str:
        assert ignored_prompt
        raise KeyboardInterrupt

    def unused_secret_input(ignored_prompt: str) -> str:
        assert ignored_prompt
        return "unused"

    output_stream = io.StringIO()
    registration_runtime = RegistrationRuntime(
        options=_options(),
        console=Console(file=output_stream, color_system=None, width=120),
        input_line=cancelled_input,
        input_secret=unused_secret_input,
        environment={},
    )

    assert run_main_loop(registration_runtime) == 130
    assert "Registration cancelled." in output_stream.getvalue()
