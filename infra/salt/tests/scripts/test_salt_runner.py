"""Tests for the Salt runner."""

from __future__ import annotations

# pyright: reportPrivateUsage=false

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

import pytest
import typer
from pytest import MonkeyPatch

from scripts import salt_runner


def test_local_age_identity_environment_uses_existing_identity_file(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    identity_path = tmp_path / "identity.txt"
    _ = identity_path.write_text("AGE-SECRET-KEY-EXAMPLE\n", encoding="utf-8")
    monkeypatch.setenv(
        salt_runner.AGE_IDENTITY_FILE_ENVIRONMENT_KEY,
        str(identity_path),
    )
    monkeypatch.delenv(salt_runner.AGE_IDENTITY_ENVIRONMENT_KEY, raising=False)

    with salt_runner._local_age_identity_environment() as environment:
        assert environment == {
            salt_runner.AGE_IDENTITY_FILE_ENVIRONMENT_KEY: str(identity_path)
        }

    assert identity_path.read_text(encoding="utf-8") == "AGE-SECRET-KEY-EXAMPLE\n"


def test_local_age_identity_environment_writes_environment_identity_to_temporary_file(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.delenv(salt_runner.AGE_IDENTITY_FILE_ENVIRONMENT_KEY, raising=False)
    monkeypatch.setenv(
        salt_runner.AGE_IDENTITY_ENVIRONMENT_KEY,
        "AGE-SECRET-KEY-EXAMPLE",
    )

    with salt_runner._local_age_identity_environment() as environment:
        identity_path = Path(environment[salt_runner.AGE_IDENTITY_FILE_ENVIRONMENT_KEY])
        assert identity_path.read_text(encoding="utf-8") == ("AGE-SECRET-KEY-EXAMPLE\n")
        assert identity_path.stat().st_mode & 0o777 == 0o600

    assert not identity_path.exists()


def test_sudo_environment_arguments_include_identity_file_without_identity_string(
    tmp_path: Path,
) -> None:
    identity_path = tmp_path / "identity.txt"

    arguments = salt_runner._sudo_environment_arguments(
        {salt_runner.AGE_IDENTITY_FILE_ENVIRONMENT_KEY: str(identity_path)}
    )

    assert (
        f"{salt_runner.AGE_IDENTITY_FILE_ENVIRONMENT_KEY}={identity_path}" in arguments
    )
    assert not any("AGE-SECRET-KEY" in argument for argument in arguments)


def test_python_path_includes_editable_source_paths(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    site_packages_path = tmp_path / "site-packages"
    site_packages_path.mkdir()
    _ = (site_packages_path / "__editable__.local-0.1.0.pth").write_text(
        "/example/local/src\n"
        "import __editable___saltstack_0_1_0_finder; "
        "__editable___saltstack_0_1_0_finder.install()\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(salt_runner, "SALT_SITE_PACKAGES", site_packages_path)

    assert salt_runner._python_path().split(":") == [
        str(salt_runner.PROJECT_DIRECTORY),
        str(site_packages_path),
        "/example/local/src",
    ]


def test_ssh_apply_command_clears_roster_host_keys_before_state(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    events: list[tuple[str, tuple[str, ...]]] = []
    roster_path = tmp_path / "roster"
    _ = roster_path.write_text(
        "target-one:\n  host: one.example.test\n"
        "target-two:\n  host: two.example.test\n  port: 2222\n"
        "other-target:\n  host: other.example.test\n",
        encoding="utf-8",
    )

    def ensure_salt_python() -> None:
        events.append(("ensure", ()))

    def run_subprocess(command_arguments: Sequence[str]) -> int:
        events.append(("subprocess", tuple(command_arguments)))
        return 0

    def run_ssh_state(
        target_name: str,
        state_name: str | None,
        *,
        test_mode: bool,
        state_output: str,
        state_verbose: str,
        observe: bool,
    ) -> int:
        assert state_name is None
        assert test_mode is False
        assert observe is False
        events.append(
            (
                "state",
                (target_name, state_output, state_verbose),
            )
        )
        return 0

    monkeypatch.setattr(salt_runner, "ROSTER_PATH", roster_path)
    monkeypatch.setattr(salt_runner, "_ensure_salt_python", ensure_salt_python)
    monkeypatch.setattr(salt_runner, "_run_subprocess", run_subprocess)
    monkeypatch.setattr(salt_runner, "_run_ssh_state", run_ssh_state)

    with pytest.raises(typer.Exit) as typer_exit:
        salt_runner.ssh_apply_command("target-*", clear_host_key=True)

    assert typer_exit.value.exit_code == 0
    assert events == [
        ("ensure", ()),
        ("subprocess", ("ssh-keygen", "-R", "one.example.test")),
        ("subprocess", ("ssh-keygen", "-R", "two.example.test")),
        ("subprocess", ("ssh-keygen", "-R", "[two.example.test]:2222")),
        (
            "state",
            (
                "target-*",
                salt_runner.DEFAULT_STATE_OUTPUT,
                salt_runner.DEFAULT_STATE_VERBOSE,
            ),
        ),
    ]


def test_ssh_observer_command_uses_roster_connection_options() -> None:
    command_arguments = salt_runner._ssh_observer_command(
        {
            "host": "example.test",
            "user": "admin",
            "port": 2222,
            "ssh_options": ["ServerAliveInterval=15", "StrictHostKeyChecking=yes"],
        }
    )

    assert command_arguments[:-1] == [
        "ssh",
        "-n",
        "-T",
        "-p",
        "2222",
        "-o",
        "ServerAliveInterval=15",
        "-o",
        "StrictHostKeyChecking=yes",
        "admin@example.test",
    ]
    assert command_arguments[-1].startswith("sh -c ")
    assert "journalctl" in command_arguments[-1]
    assert "ps axww" in command_arguments[-1]


def test_run_ssh_state_wraps_salt_with_observer(
    monkeypatch: MonkeyPatch,
) -> None:
    events: list[tuple[str, tuple[str, ...]]] = []

    @contextmanager
    def ssh_observers(target_name: str) -> Iterator[None]:
        events.append(("observe-start", (target_name,)))
        try:
            yield
        finally:
            events.append(("observe-stop", (target_name,)))

    def run_subprocess(command_arguments: Sequence[str]) -> int:
        events.append(("subprocess", tuple(command_arguments)))
        return 7

    monkeypatch.setattr(salt_runner, "_ssh_observers", ssh_observers)
    monkeypatch.setattr(salt_runner, "_run_subprocess", run_subprocess)
    monkeypatch.setattr(
        salt_runner,
        "SALT_PYTHON",
        Path("/example/python"),
    )

    assert (
        salt_runner._run_ssh_state(
            "target",
            "state.name",
            test_mode=True,
            state_output="changes",
            state_verbose="false",
            observe=True,
        )
        == 7
    )
    assert events == [
        ("observe-start", ("target",)),
        (
            "subprocess",
            (
                "/example/python",
                "-m",
                "scripts.salt_runner",
                "_ssh",
                "--config-dir=config",
                "--state-output=changes",
                "--state-verbose=false",
                "target",
                "--state-verbose=false",
                "state.apply",
                "state.name",
                "test=true",
            ),
        ),
        ("observe-stop", ("target",)),
    ]
