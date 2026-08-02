"""Tests for Bash hook CLI behavior."""

from __future__ import annotations

import contextlib
import importlib
import io
import shlex
import shutil
import subprocess
import textwrap
import time
from pathlib import Path

import pytest
from typer._click.exceptions import BadParameter

from maker_guide.cli.hook import render_bash_init, run


def _payload_before(command: str) -> dict[str, object]:
    return {
        "version": 1,
        "type": "preexec",
        "cwd": str(Path.cwd()),
        "command": command,
        "shell": "bash",
    }


def _payload_after(command: str, exit_status: int) -> dict[str, object]:
    return {
        "version": 1,
        "type": "postexec",
        "cwd": str(Path.cwd()),
        "command": command,
        "shell": "bash",
        "exit_status": exit_status,
    }


def _run_bash_hook_harness(
    tmp_path: Path,
    setup_commands: str,
    command_commands: str,
    init_source_count: int = 1,
    expected_event_count: int | None = None,
) -> list[str]:
    init_path = tmp_path / "maker-guide-init.bash"
    script_path = tmp_path / "hook-harness.bash"
    log_path = tmp_path / "hook-events.log"
    init_path.write_text(render_bash_init("maker_guide_hook"), encoding="utf-8")
    script_path.write_text(
        _bash_hook_script(
            init_path,
            log_path,
            setup_commands,
            command_commands,
            init_source_count,
        ),
        encoding="utf-8",
    )
    bash_path = shutil.which("bash")
    assert bash_path is not None

    completed_process = subprocess.run(
        [bash_path, "--noprofile", "--norc", str(script_path)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed_process.returncode == 0, completed_process.stderr
    if expected_event_count is not None:
        return _wait_for_log_lines(log_path, expected_event_count)
    if not log_path.exists():
        return []
    return log_path.read_text(encoding="utf-8").splitlines()


def _wait_for_log_lines(log_path: Path, expected_event_count: int) -> list[str]:
    deadline = time.monotonic() + 1
    while time.monotonic() < deadline:
        if log_path.exists():
            lines = log_path.read_text(encoding="utf-8").splitlines()
            if len(lines) >= expected_event_count:
                return lines
        time.sleep(0.01)
    if not log_path.exists():
        return []
    return log_path.read_text(encoding="utf-8").splitlines()


def _bash_hook_script(
    init_path: Path,
    log_path: Path,
    setup_commands: str,
    command_commands: str,
    init_source_count: int,
) -> str:
    return textwrap.dedent(
        f"""\
        set -euo pipefail
        set -o history
        shopt -s expand_aliases
        __bp_delay_install=1
        MAKER_GUIDE_HOOK_LOG={shlex.quote(str(log_path))}
        maker_guide_hook() {{
            printf '%s\\n' "$*" >> "$MAKER_GUIDE_HOOK_LOG"
        }}
        {_source_commands(init_path, init_source_count)}
        {textwrap.dedent(setup_commands).strip()}
        __bp_install "$_"
        {textwrap.dedent(command_commands).strip()}
        """
    )


def _source_commands(init_path: Path, init_source_count: int) -> str:
    return "\n".join([f"source {shlex.quote(str(init_path))}"] * init_source_count)


def test_hook_module_imports() -> None:
    """Packaging must not ship syntax errors in the hook entrypoint."""
    assert importlib.import_module("maker_guide.cli.hook") is not None


def test_before_hook_sends_event_and_never_blocks() -> None:
    """Preexec events are telemetry-only."""
    captured_payloads: list[dict[str, object]] = []

    def sender(
        _socket_path: Path,
        _timeout_seconds: float,
        payload: dict[str, object],
    ) -> None:
        captured_payloads.append(payload)

    status = run(["--socket", "km.sock", "before", "rm -rf /tmp/nope"], sender)

    assert status == 0
    payload = captured_payloads[0]
    assert isinstance(payload.pop("event_id"), str)
    assert isinstance(payload.pop("timestamp"), str)
    tty = payload.pop("tty")
    assert isinstance(tty, str | None)
    assert payload == _payload_before("rm -rf /tmp/nope")


def test_before_hook_fails_open_when_daemon_is_unavailable() -> None:
    """Transport failures must not break normal shell usage."""

    def sender(
        _socket_path: Path,
        _timeout_seconds: float,
        _payload: dict[str, object],
    ) -> None:
        return

    assert run(["before", "echo hello"], sender) == 0


def test_after_hook_sends_exit_status_and_never_blocks() -> None:
    """Postexec events include status but cannot prevent a completed command."""
    captured_payloads: list[dict[str, object]] = []

    def sender(
        _socket_path: Path,
        _timeout_seconds: float,
        payload: dict[str, object],
    ) -> None:
        captured_payloads.append(payload)

    status = run(["after", "2", "make test"], sender)

    assert status == 0
    payload = captured_payloads[0]
    assert isinstance(payload.pop("event_id"), str)
    assert isinstance(payload.pop("timestamp"), str)
    tty = payload.pop("tty")
    assert isinstance(tty, str | None)
    assert payload == _payload_after("make test", 2)


@pytest.mark.parametrize("timeout_seconds", ["0", "-0.1"])
def test_hook_rejects_non_positive_timeout(timeout_seconds: str) -> None:
    """Hook socket timeout must not silently become non-blocking or invalid."""
    with pytest.raises(BadParameter, match=r"x>=0\.001"):
        run(["--timeout", timeout_seconds, "before", "true"])


@pytest.mark.parametrize("exit_status", ["-1", "256"])
def test_after_hook_rejects_exit_status_outside_shell_range(exit_status: str) -> None:
    """Post-command status is constrained to the shell byte-sized range."""
    with pytest.raises(BadParameter):
        run(["after", exit_status, "true"])


def test_init_bash_prints_eval_safe_hook_script() -> None:
    """The init subcommand prints Bash code for eval."""
    output = io.StringIO()

    with contextlib.redirect_stdout(output):
        status = run(["init", "bash"])

    assert status == 0
    assert output.getvalue() == render_bash_init()


def test_bash_init_does_not_create_visible_background_jobs() -> None:
    """Telemetry must not produce interactive job-completion messages."""
    bash_init = render_bash_init()

    assert '    ( "$@" >/dev/null 2>&1 & )' in bash_init
    assert "__MAKER_GUIDE_PENDING_AFTER_PROCESS" not in bash_init


def test_bash_init_skips_postexec_without_preexec(tmp_path: Path) -> None:
    """Prompt setup must not emit empty command events."""
    assert _run_bash_hook_harness(tmp_path, "", "") == []


def test_bash_init_emits_one_event_pair_for_alias(tmp_path: Path) -> None:
    """Alias expansion can trigger multiple DEBUG traps but only one event pair."""
    events = _run_bash_hook_harness(
        tmp_path,
        """
        alias kmlist='printf alias-output'
        history -s 'kmlist'
        """,
        """
        kmlist >/dev/null
        __bp_precmd_invoke_cmd force
        """,
        expected_event_count=2,
    )

    assert len(events) == 2
    before_events = [event for event in events if event.startswith("before ")]
    after_events = [event for event in events if event.startswith("after 0 ")]
    assert len(before_events) == 1
    assert len(after_events) == 1
    assert before_events[0].removeprefix("before ") == after_events[0].removeprefix("after 0 ")
    assert "alias-output" in before_events[0]


def test_bash_init_logs_full_pipeline_command(tmp_path: Path) -> None:
    """Pipeline telemetry uses the full command from bash-preexec."""
    events = _run_bash_hook_harness(
        tmp_path,
        "history -s 'printf foo | sed s/foo/bar/'",
        """
        printf foo | sed s/foo/bar/ >/dev/null
        __bp_precmd_invoke_cmd force
        """,
        expected_event_count=2,
    )

    assert events in [
        [
            "before printf foo | sed s/foo/bar/",
            "after 0 printf foo | sed s/foo/bar/",
        ],
        ["before printf foo", "after 0 printf foo"],
    ]


def test_bash_init_is_idempotent_when_sourced_twice(tmp_path: Path) -> None:
    """Repeated eval must not append duplicate project hooks."""
    assert _run_bash_hook_harness(
        tmp_path,
        """
        preexec_count=0
        for hook_function in "${preexec_functions[@]:-}"; do
            if [[ "$hook_function" == "__maker_guide_preexec" ]]; then
                preexec_count=$((preexec_count + 1))
            fi
        done

        precmd_count=0
        for hook_function in "${precmd_functions[@]:-}"; do
            if [[ "$hook_function" == "__maker_guide_precmd" ]]; then
                precmd_count=$((precmd_count + 1))
            fi
        done

        printf 'counts %s %s\n' "$preexec_count" "$precmd_count" >> "$MAKER_GUIDE_HOOK_LOG"
        """,
        "",
        init_source_count=2,
    ) == ["counts 1 1"]
