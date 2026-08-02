"""Tests for the Kolam Ayer Makers classroom LLDAP password reset helper."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

from tests.support.paths import SALTSTACK_DIRECTORY


def _load_script() -> ModuleType:
    loader = importlib.machinery.SourceFileLoader(
        "lldap_set_password",
        str(
            SALTSTACK_DIRECTORY
            / "states/roles/kam-classroom/files/lldap_set_password.py"
        ),
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise AssertionError("Could not load lldap-set-password script")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_argument_parser_accepts_username(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that only a username is required."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lldap-set-password",
            "alice",
        ],
    )

    arguments = _load_script().parse_arguments()

    assert arguments.username == "alice"
    assert arguments.password_stdin is False
    assert arguments.check is False
    assert arguments.base_url == "http://127.0.0.1:17170/"
    assert arguments.admin_username == "admin"
    assert arguments.environment_file == "/etc/lldap/lldap.env"
    assert arguments.pwscore_command == "/usr/bin/pwscore"


def test_generate_password_uses_debian_diceware(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that generated passwords come from the Debian diceware package."""
    script = _load_script()
    calls: list[list[str]] = []

    def run(
        arguments: list[str],
        *,
        check: bool,
        stdout: int,
        stderr: int,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(arguments)
        assert check is True
        assert stdout == subprocess.PIPE
        assert stderr == subprocess.PIPE
        assert text is True
        return subprocess.CompletedProcess(
            arguments,
            0,
            stdout="alpha-bravo-charlie-delta-echo-foxtrot\n",
            stderr="",
        )

    monkeypatch.setattr(script.subprocess, "run", run)

    assert script.generate_password() == "alpha-bravo-charlie-delta-echo-foxtrot"
    assert calls == [
        ["/usr/bin/diceware", "--no-caps", "--delimiter", "-", "--num", "6"]
    ]


def test_password_strength_uses_pwscore(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that password validation delegates to libpwquality."""
    script = _load_script()
    calls: list[dict[str, object]] = []

    def run(
        arguments: list[str],
        *,
        check: bool,
        input: str,
        stdout: int,
        stderr: int,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls.append({"arguments": arguments, "input": input})
        assert check is False
        assert stdout == subprocess.PIPE
        assert stderr == subprocess.PIPE
        assert text is True
        return subprocess.CompletedProcess(arguments, 1, stdout="", stderr="too weak\n")

    monkeypatch.setattr(script.subprocess, "run", run)

    assert (
        script.password_strength_error(
            "/usr/bin/pwscore",
            "alice",
            "short",
        )
        == "too weak"
    )
    assert calls == [{"arguments": ["/usr/bin/pwscore"], "input": "short\n"}]


def test_validate_password_rejects_username_derived_password() -> None:
    """Test that helper resets reject passwords containing the username."""
    script = _load_script()

    with pytest.raises(script.LldapError) as error:
        script.validate_password("/usr/bin/pwscore", "alice", "prefix-alice-suffix")

    assert str(error.value) == "Password rejected: It contains the username."


def test_generate_compliant_password_retries_after_pwquality_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that generated passwords are checked against the active policy."""
    script = _load_script()
    generated_passwords = iter(["weak-password", "strong-password"])
    checked_passwords: list[str] = []

    monkeypatch.setattr(script, "generate_password", lambda: next(generated_passwords))

    def password_strength_error(
        pwscore_command: str,
        username: str,
        password: str,
    ) -> str | None:
        assert pwscore_command == "/usr/bin/pwscore"
        assert username == "alice"
        checked_passwords.append(password)
        if password == "weak-password":
            return "too weak"
        return None

    monkeypatch.setattr(script, "password_strength_error", password_strength_error)

    assert (
        script.generate_compliant_password("/usr/bin/pwscore", "alice")
        == "strong-password"
    )
    assert checked_passwords == ["weak-password", "strong-password"]


def test_set_password_calls_lldap_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that password resets delegate to the packaged LLDAP helper."""
    script = _load_script()
    calls: list[dict[str, object]] = []

    def run(
        arguments: list[str],
        *,
        env: dict[str, str],
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls.append({"arguments": arguments, "password": env["LLDAP_USER_PASSWORD"]})
        assert check is True
        return subprocess.CompletedProcess(arguments, 0)

    monkeypatch.setattr(script.subprocess, "run", run)

    script.set_password("http://127.0.0.1:17170/", "token", "alice", "secret")

    assert calls == [
        {
            "arguments": [
                "/usr/local/bin/lldap_set_password",
                "--base-url",
                "http://127.0.0.1:17170/",
                "--token",
                "token",
                "--username",
                "alice",
            ],
            "password": "secret",
        }
    ]


def test_main_resets_generated_password_and_prints_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that missing stdin generates and prints a one-time password."""
    script = _load_script()
    environment_file = tmp_path / "lldap.env"
    _ = environment_file.write_text(
        "LLDAP_LDAP_USER_PASS=admin-secret\n", encoding="utf-8"
    )
    calls: list[dict[str, str]] = []

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lldap-set-password",
            "alice",
            "--environment-file",
            str(environment_file),
        ],
    )

    def generate_compliant_password(pwscore_command: str, username: str) -> str:
        assert pwscore_command == "/usr/bin/pwscore"
        assert username == "alice"
        return "generated-password"

    monkeypatch.setattr(
        script, "generate_compliant_password", generate_compliant_password
    )

    def login(base_url: str, username: str, password: str) -> str:
        calls.append({"base_url": base_url, "username": username, "password": password})
        return "token"

    monkeypatch.setattr(script, "login", login)

    def set_password(
        base_url: str,
        token: str,
        username: str,
        password: str,
    ) -> None:
        calls.append(
            {
                "base_url": base_url,
                "token": token,
                "username": username,
                "password": password,
            }
        )

    monkeypatch.setattr(script, "set_password", set_password)

    assert script.main() == 0
    assert calls == [
        {
            "base_url": "http://127.0.0.1:17170/",
            "username": "admin",
            "password": "admin-secret",
        },
        {
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "username": "alice",
            "password": "generated-password",
        },
    ]
    assert capsys.readouterr().out == "alice\ngenerated-password\n"


def test_main_resets_password_from_stdin_without_printing_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that stdin passwords are not echoed."""
    script = _load_script()
    environment_file = tmp_path / "lldap.env"
    _ = environment_file.write_text(
        "LLDAP_LDAP_USER_PASS=admin-secret\n", encoding="utf-8"
    )
    calls: list[dict[str, str]] = []
    validation_calls: list[dict[str, str]] = []

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lldap-set-password",
            "alice",
            "--password-stdin",
            "--environment-file",
            str(environment_file),
        ],
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO("stdin-password\n"))

    def validate_password(
        pwscore_command: str,
        username: str,
        password: str,
    ) -> None:
        validation_calls.append(
            {
                "pwscore_command": pwscore_command,
                "username": username,
                "password": password,
            }
        )

    monkeypatch.setattr(script, "validate_password", validate_password)

    def login(base_url: str, username: str, password: str) -> str:
        assert base_url == "http://127.0.0.1:17170/"
        assert username == "admin"
        assert password == "admin-secret"
        return "token"

    monkeypatch.setattr(script, "login", login)

    def set_password(
        base_url: str,
        token: str,
        username: str,
        password: str,
    ) -> None:
        calls.append(
            {
                "base_url": base_url,
                "token": token,
                "username": username,
                "password": password,
            }
        )

    monkeypatch.setattr(script, "set_password", set_password)

    assert script.main() == 0
    assert calls == [
        {
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "username": "alice",
            "password": "stdin-password",
        }
    ]
    assert validation_calls == [
        {
            "pwscore_command": "/usr/bin/pwscore",
            "username": "alice",
            "password": "stdin-password",
        }
    ]
    assert capsys.readouterr().out == "alice\n"


def test_main_checks_password_from_stdin_without_admin_secret(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that check mode only verifies the target user's password."""
    script = _load_script()
    calls: list[dict[str, str]] = []

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lldap-set-password",
            "alice",
            "--password-stdin",
            "--check",
            "--environment-file",
            str(tmp_path / "missing.env"),
        ],
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO("current-password\n"))

    def validate_password(
        pwscore_command: str,
        username: str,
        password: str,
    ) -> None:
        raise AssertionError(
            f"check mode should not validate {username} with {pwscore_command}: {password}"
        )

    monkeypatch.setattr(script, "validate_password", validate_password)

    def login(base_url: str, username: str, password: str) -> str:
        calls.append({"base_url": base_url, "username": username, "password": password})
        return "token"

    monkeypatch.setattr(script, "login", login)

    assert script.main() == 0
    assert calls == [
        {
            "base_url": "http://127.0.0.1:17170/",
            "username": "alice",
            "password": "current-password",
        }
    ]
    assert capsys.readouterr().out == ""
