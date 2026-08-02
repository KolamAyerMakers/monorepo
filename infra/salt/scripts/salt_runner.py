#!/usr/bin/env -S uv run python
"""Command-line wrapper for repeatable local and SSH Salt runs."""
# pyright: reportMissingTypeStubs=false

from __future__ import annotations

import fnmatch
import importlib
import os
import shlex
import signal
import subprocess
import sys
import tempfile
import threading
import warnings
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Literal, Protocol, cast

import typer

PROJECT_DIRECTORY = Path(__file__).resolve().parents[1]
SALT_PYTHON = Path(os.environ.get("SALT_PYTHON", sys.executable)).resolve()
SALT_SITE_PACKAGES = next(
    (PROJECT_DIRECTORY / ".venv/lib").glob("python*/site-packages")
).resolve()
DEFAULT_STATE_OUTPUT = os.environ.get("SALT_STATE_OUTPUT", "changes")
DEFAULT_STATE_VERBOSE = os.environ.get("SALT_STATE_VERBOSE", "false")
DEFAULT_UV_CACHE_DIRECTORY = os.environ.get("UV_CACHE_DIR", "/tmp/uv-cache")
DEFAULT_XDG_DATA_HOME = os.environ.get("XDG_DATA_HOME", "/tmp/xdg-data")
AGE_IDENTITY_ENVIRONMENT_KEY = "AGE_IDENTITY"
AGE_IDENTITY_FILE_ENVIRONMENT_KEY = "AGE_IDENTITY_FILE"
LOCAL_AGE_IDENTITY_COMMAND = ("pass", "infra/saltstack/age-identity/private")
ROSTER_PATH = PROJECT_DIRECTORY / "config/roster"
APP_CONTEXT_SETTINGS = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
}
WarningAction = Literal["default", "error", "ignore", "always", "module", "once"]
WARNING_ACTIONS: set[WarningAction] = {
    "default",
    "error",
    "ignore",
    "always",
    "module",
    "once",
}
CTRL_C_MESSAGE = "Exiting gracefully on Ctrl-c"
DEFAULT_SSH_USER = "root"
DEFAULT_SSH_PORT = 22


class _YamlModule(Protocol):
    def safe_load(self, value: str) -> object: ...
SSH_OBSERVER_SCRIPT = r"""
set +e
cleanup() {
    for process_id in $(jobs -p); do
        kill "$process_id" 2>/dev/null || true
    done
}
trap 'cleanup; exit 0' INT TERM HUP
printf 'observer started %s\n' "$(date -Is 2>/dev/null || date)"
for log_file in /var/log/dpkg.log /var/log/apt/term.log /var/log/apt/history.log /var/log/syslog /var/log/salt/minion; do
    if [ -r "$log_file" ]; then
        tail -n 0 -F "$log_file" &
    fi
done
if command -v journalctl >/dev/null 2>&1; then
    journalctl -f -n 0 -o short-iso --no-pager &
fi
while :; do
    printf '\n=== observe %s ===\n' "$(date -Is 2>/dev/null || date)"
    ps axww -o pid,ppid,user,stat,etime,args 2>/dev/null | grep -E 'salt|apt|dpkg|systemctl|systemd-run|python|/var/tmp/\.' | grep -v grep || true
    for directory in /var/tmp/.[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f] /var/tmp/.*_salt; do
        if [ -d "$directory" ]; then
            printf 'salt-thin %s\n' "$directory"
            if [ -r "$directory/running_data/salt-call.log" ]; then
                printf 'salt-log %s\n' "$directory/running_data/salt-call.log"
            fi
        fi
    done
    sleep 2
done
""".strip()


def _configure_warnings() -> None:
    action_name = os.environ.get("SALT_DEPRECATION_ACTION", "ignore")
    if action_name not in WARNING_ACTIONS:
        message = f"Unsupported SALT_DEPRECATION_ACTION: {action_name}"
        raise RuntimeError(message)
    action: WarningAction = action_name

    # Salt re-enables its own DeprecationWarnings during import, so override
    # that policy only after the package is loaded.
    _ = importlib.import_module("salt")

    warnings.filterwarnings(
        action,
        "",
        DeprecationWarning,
        r"^(salt|salt\.(.*))$",
    )


def _ensure_salt_python() -> None:
    if not SALT_PYTHON.is_file():
        message = f"salt python executable not found: {SALT_PYTHON}"
        raise RuntimeError(message)
    if not SALT_SITE_PACKAGES.is_dir():
        message = f"salt site-packages directory not found: {SALT_SITE_PACKAGES}"
        raise RuntimeError(message)


def _configure_python_imports() -> None:
    for python_path_entry in reversed(_python_path().split(os.pathsep)):
        if python_path_entry not in sys.path:
            sys.path.insert(0, python_path_entry)


def _raise_keyboard_interrupt(signum: int, frame: object) -> None:
    del signum, frame
    raise KeyboardInterrupt()


def _print_ctrl_c_message() -> None:
    print(CTRL_C_MESSAGE, file=sys.stderr, flush=True)


def _handle_salt_system_exit(system_exit: SystemExit) -> int:
    exit_code = system_exit.code
    if isinstance(exit_code, str) and CTRL_C_MESSAGE in exit_code:
        _print_ctrl_c_message()
        return 130
    if isinstance(exit_code, int):
        return exit_code
    raise system_exit


def _run_salt_entrypoint(command_name: str, salt_arguments: Sequence[str]) -> int:
    sys.argv = [f"salt-{command_name}", *salt_arguments]
    _configure_python_imports()
    _configure_warnings()
    original_sigint_handler = signal.getsignal(signal.SIGINT)
    _ = signal.signal(signal.SIGINT, _raise_keyboard_interrupt)

    try:
        if command_name == "call":
            from salt.scripts import salt_call

            salt_call()
            return 0

        if command_name == "ssh":
            from salt.scripts import salt_ssh

            salt_ssh()
            return 0

        raise ValueError(f"Unsupported Salt command: {command_name}")
    except KeyboardInterrupt:
        _print_ctrl_c_message()
        return 130
    except SystemExit as system_exit:
        return _handle_salt_system_exit(system_exit)
    finally:
        _ = signal.signal(signal.SIGINT, original_sigint_handler)


def _run_subprocess(command_arguments: Sequence[str]) -> int:
    completed_process = subprocess.run(
        command_arguments,
        check=False,
        cwd=PROJECT_DIRECTORY,
        env={
            **os.environ,
            "PYTHONPATH": _python_path(),
            "UV_CACHE_DIR": DEFAULT_UV_CACHE_DIRECTORY,
            "XDG_DATA_HOME": DEFAULT_XDG_DATA_HOME,
        },
    )
    return completed_process.returncode


def _run_local_subprocess(command_arguments: Sequence[str]) -> int:
    completed_process = subprocess.run(
        command_arguments,
        check=False,
        cwd=PROJECT_DIRECTORY,
        env={
            **os.environ,
            "PYTHONPATH": _python_path(),
            "UV_CACHE_DIR": DEFAULT_UV_CACHE_DIRECTORY,
            "XDG_DATA_HOME": DEFAULT_XDG_DATA_HOME,
        },
    )
    return completed_process.returncode


def _salt_runner_command() -> list[str]:
    return [str(SALT_PYTHON), "-m", "scripts.salt_runner"]


def _editable_source_paths() -> list[str]:
    source_paths: list[str] = []
    for editable_path_file in sorted(SALT_SITE_PACKAGES.glob("__editable__.*.pth")):
        for line in editable_path_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("/"):
                source_paths.append(line)
    return source_paths


def _python_path() -> str:
    return os.pathsep.join(
        [
            str(PROJECT_DIRECTORY),
            str(SALT_SITE_PACKAGES),
            *_editable_source_paths(),
        ]
    )


def _build_state_arguments(
    state_name: str | None,
    *,
    test_mode: bool,
    state_output: str,
    state_verbose: str,
) -> list[str]:
    state_arguments = [
        "--config-dir=config",
        f"--state-output={state_output}",
        f"--state-verbose={state_verbose}",
        "state.apply",
    ]
    if state_name:
        state_arguments.append(state_name)
    if test_mode:
        state_arguments.append("test=true")
    return state_arguments


def _local_root_arguments() -> list[str]:
    # Override file_roots/pillar_roots with absolute paths so that Salt's
    # post-write diff rendering in file.managed does not fail on the relative
    # paths declared in config/minion.
    return [
        f"--file-root={PROJECT_DIRECTORY / 'states'}",
        f"--pillar-root={PROJECT_DIRECTORY / 'pillar'}",
    ]


def _read_local_age_identity() -> str:
    completed_process = subprocess.run(
        LOCAL_AGE_IDENTITY_COMMAND,
        check=False,
        cwd=PROJECT_DIRECTORY,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed_process.returncode != 0:
        message = completed_process.stderr.strip() or completed_process.stdout.strip()
        if message:
            raise RuntimeError(f"failed to read local age identity: {message}")
        raise RuntimeError("failed to read local age identity")

    identity = completed_process.stdout.strip()
    if not identity:
        raise RuntimeError("local age identity command returned no identity")
    return identity


@contextmanager
def _local_age_identity_environment() -> Iterator[dict[str, str]]:
    identity_file = os.environ.get(AGE_IDENTITY_FILE_ENVIRONMENT_KEY)
    if identity_file:
        yield {AGE_IDENTITY_FILE_ENVIRONMENT_KEY: identity_file}
        return

    identity = (
        os.environ.get(AGE_IDENTITY_ENVIRONMENT_KEY) or _read_local_age_identity()
    )
    temporary_identity_path: Path | None = None
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        prefix="saltstack-age-identity-",
        delete=False,
    ) as temporary_identity_file:
        temporary_identity_path = Path(temporary_identity_file.name)
        _ = temporary_identity_file.write(identity.strip())
        _ = temporary_identity_file.write("\n")

    temporary_identity_path.chmod(0o600)
    try:
        yield {AGE_IDENTITY_FILE_ENVIRONMENT_KEY: str(temporary_identity_path)}
    finally:
        temporary_identity_path.unlink(missing_ok=True)


def _sudo_environment_arguments(
    extra_environment: Mapping[str, str],
) -> list[str]:
    return [
        f"PYTHONPATH={_python_path()}",
        f"UV_CACHE_DIR={DEFAULT_UV_CACHE_DIRECTORY}",
        f"XDG_DATA_HOME={DEFAULT_XDG_DATA_HOME}",
        *[
            f"{environment_key}={environment_value}"
            for environment_key, environment_value in sorted(extra_environment.items())
        ],
    ]


def _run_local_sync(
    state_output: str,
    state_verbose: str,
    extra_environment: Mapping[str, str],
) -> int:
    return _run_local_subprocess(
        [
            "sudo",
            "env",
            *_sudo_environment_arguments(extra_environment),
            *_salt_runner_command(),
            "_call",
            "--config-dir=config",
            *_local_root_arguments(),
            f"--state-output={state_output}",
            f"--state-verbose={state_verbose}",
            "state.single",
            "saltutil.sync_all",
            "name=sync_all",
        ]
    )


def _run_local_state(
    state_name: str | None,
    *,
    test_mode: bool,
    state_output: str,
    state_verbose: str,
) -> int:
    with _local_age_identity_environment() as extra_environment:
        sync_exit_code = _run_local_sync(
            state_output,
            state_verbose,
            extra_environment,
        )
        if sync_exit_code != 0:
            return sync_exit_code

        state_arguments = _build_state_arguments(
            state_name,
            test_mode=test_mode,
            state_output=state_output,
            state_verbose=state_verbose,
        )
        salt_call_arguments = [
            state_arguments[0],
            *_local_root_arguments(),
            *state_arguments[1:],
        ]
        return _run_local_subprocess(
            [
                "sudo",
                "env",
                *_sudo_environment_arguments(extra_environment),
                *_salt_runner_command(),
                "_call",
                *salt_call_arguments,
            ]
        )


def _run_ssh_state(
    target_name: str,
    state_name: str | None,
    *,
    test_mode: bool,
    state_output: str,
    state_verbose: str,
    observe: bool,
) -> int:
    command_arguments = [
        *_salt_runner_command(),
        "_ssh",
        "--config-dir=config",
        f"--state-output={state_output}",
        f"--state-verbose={state_verbose}",
        target_name,
        *_build_state_arguments(
            state_name,
            test_mode=test_mode,
            state_output=state_output,
            state_verbose=state_verbose,
        )[2:],
    ]
    if not observe:
        return _run_subprocess(command_arguments)

    with _ssh_observers(target_name):
        return _run_subprocess(command_arguments)


def _matched_ssh_roster_entries(
    target_name: str,
) -> Iterator[tuple[str, Mapping[str, object]]]:
    yaml_module = cast(_YamlModule, cast(object, importlib.import_module("yaml")))
    roster = yaml_module.safe_load(ROSTER_PATH.read_text(encoding="utf-8"))
    if not isinstance(roster, Mapping):
        raise RuntimeError(f"Salt roster must be a mapping: {ROSTER_PATH}")

    for roster_name, roster_entry in roster.items():
        if not isinstance(roster_name, str):
            continue
        if not fnmatch.fnmatch(roster_name, target_name):
            continue
        if not isinstance(roster_entry, Mapping):
            continue
        yield roster_name, cast(Mapping[str, object], roster_entry)


def _ssh_known_host_names(target_name: str) -> list[str]:
    known_host_names: list[str] = []
    for _, roster_entry in _matched_ssh_roster_entries(target_name):
        host_name = roster_entry.get("host")
        if not isinstance(host_name, str) or host_name == "":
            continue

        known_host_names.append(host_name)
        port = roster_entry.get("port")
        if isinstance(port, int) and port != 22:
            known_host_names.append(f"[{host_name}]:{port}")

    if known_host_names:
        return list(dict.fromkeys(known_host_names))

    message = f"no Salt roster hosts match target {target_name!r}"
    raise RuntimeError(message)


def _ssh_observer_command(roster_entry: Mapping[str, object]) -> list[str]:
    host_name = roster_entry.get("host")
    if not isinstance(host_name, str) or host_name == "":
        raise RuntimeError("Salt roster entry has no host")

    user_name = roster_entry.get("user")
    if not isinstance(user_name, str) or user_name == "":
        user_name = DEFAULT_SSH_USER

    port = roster_entry.get("port")
    port_number = port if isinstance(port, int) else DEFAULT_SSH_PORT
    command_arguments = ["ssh", "-n", "-T", "-p", str(port_number)]
    ssh_options = roster_entry.get("ssh_options")
    if isinstance(ssh_options, Sequence) and not isinstance(ssh_options, str):
        for ssh_option in ssh_options:
            if isinstance(ssh_option, str):
                command_arguments.extend(["-o", ssh_option])

    command_arguments.extend(
        [f"{user_name}@{host_name}", f"sh -c {shlex.quote(SSH_OBSERVER_SCRIPT)}"]
    )
    return command_arguments


def _stream_ssh_observer_output(
    roster_name: str,
    observer_process: subprocess.Popen[str],
) -> None:
    observer_stdout = observer_process.stdout
    if observer_stdout is None:
        return

    for output_line in observer_stdout:
        print(
            f"[ssh-observe:{roster_name}] {output_line.rstrip()}",
            file=sys.stderr,
            flush=True,
        )


def _stop_ssh_observers(
    observer_processes: list[subprocess.Popen[str]],
    observer_threads: list[threading.Thread],
) -> None:
    for observer_process in observer_processes:
        if observer_process.poll() is None:
            observer_process.terminate()

    for observer_process in observer_processes:
        try:
            _ = observer_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            observer_process.kill()
            _ = observer_process.wait(timeout=3)

    for observer_thread in observer_threads:
        observer_thread.join(timeout=1)


@contextmanager
def _ssh_observers(target_name: str) -> Iterator[None]:
    observer_processes: list[subprocess.Popen[str]] = []
    observer_threads: list[threading.Thread] = []
    for roster_name, roster_entry in _matched_ssh_roster_entries(target_name):
        observer_process = subprocess.Popen(
            _ssh_observer_command(roster_entry),
            cwd=PROJECT_DIRECTORY,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        observer_thread = threading.Thread(
            target=_stream_ssh_observer_output,
            args=(roster_name, observer_process),
            daemon=True,
        )
        observer_thread.start()
        observer_processes.append(observer_process)
        observer_threads.append(observer_thread)

    if not observer_processes:
        message = f"no Salt roster hosts match target {target_name!r}"
        raise RuntimeError(message)

    try:
        yield
    finally:
        _stop_ssh_observers(observer_processes, observer_threads)


def _run_internal_subcommand() -> int:
    if len(sys.argv) < 2:
        return -1

    command_name = sys.argv[1]
    if command_name not in {"_call", "_ssh"}:
        return -1

    _ensure_salt_python()
    salt_command_name = "call" if command_name == "_call" else "ssh"
    return _run_salt_entrypoint(salt_command_name, sys.argv[2:])


application = typer.Typer(
    add_completion=False,
    context_settings=APP_CONTEXT_SETTINGS,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


@application.command("call", context_settings=APP_CONTEXT_SETTINGS)
def call_command(context: typer.Context) -> None:
    """Run a Salt call command with the repository configuration."""
    _ensure_salt_python()
    raise typer.Exit(_run_salt_entrypoint("call", list(context.args)))


@application.command("ssh", context_settings=APP_CONTEXT_SETTINGS)
def ssh_command(context: typer.Context) -> None:
    """Run a salt-ssh command with the repository configuration."""
    _ensure_salt_python()
    raise typer.Exit(_run_salt_entrypoint("ssh", list(context.args)))


@application.command("local-test")
def local_test_command(
    state_name: Annotated[str | None, typer.Argument()] = None,
    state_output: Annotated[str | None, typer.Option("--state-output")] = None,
    state_verbose: Annotated[str | None, typer.Option("--state-verbose")] = None,
) -> None:
    """Render a local Salt state in test mode."""
    _ensure_salt_python()
    raise typer.Exit(
        _run_local_state(
            state_name,
            test_mode=True,
            state_output=state_output or DEFAULT_STATE_OUTPUT,
            state_verbose=state_verbose or DEFAULT_STATE_VERBOSE,
        )
    )


@application.command("local-apply")
def local_apply_command(
    state_name: Annotated[str | None, typer.Argument()] = None,
    state_output: Annotated[str | None, typer.Option("--state-output")] = None,
    state_verbose: Annotated[str | None, typer.Option("--state-verbose")] = None,
) -> None:
    """Apply a local Salt state with the repository configuration."""
    _ensure_salt_python()
    raise typer.Exit(
        _run_local_state(
            state_name,
            test_mode=False,
            state_output=state_output or DEFAULT_STATE_OUTPUT,
            state_verbose=state_verbose or DEFAULT_STATE_VERBOSE,
        )
    )


@application.command("ssh-test")
def ssh_test_command(
    target_name: Annotated[str, typer.Argument()],
    state_name: Annotated[str | None, typer.Argument()] = None,
    state_output: Annotated[str | None, typer.Option("--state-output")] = None,
    state_verbose: Annotated[str | None, typer.Option("--state-verbose")] = None,
    observe: Annotated[
        bool,
        typer.Option("--observe", help="Stream remote logs and processes."),
    ] = False,
) -> None:
    """Render a Salt state over salt-ssh in test mode."""
    _ensure_salt_python()
    raise typer.Exit(
        _run_ssh_state(
            target_name,
            state_name,
            test_mode=True,
            state_output=state_output or DEFAULT_STATE_OUTPUT,
            state_verbose=state_verbose or DEFAULT_STATE_VERBOSE,
            observe=observe,
        )
    )


@application.command("ssh-apply")
def ssh_apply_command(
    target_name: Annotated[str, typer.Argument()],
    state_name: Annotated[str | None, typer.Argument()] = None,
    state_output: Annotated[str | None, typer.Option("--state-output")] = None,
    state_verbose: Annotated[str | None, typer.Option("--state-verbose")] = None,
    clear_host_key: Annotated[
        bool,
        typer.Option("--clear-host-key", help="Remove SSH host keys before apply."),
    ] = False,
    observe: Annotated[
        bool,
        typer.Option("--observe", help="Stream remote logs and processes."),
    ] = False,
) -> None:
    """Apply a Salt state over salt-ssh."""
    _ensure_salt_python()
    if clear_host_key:
        for known_host_name in _ssh_known_host_names(target_name):
            clear_exit_code = _run_subprocess(["ssh-keygen", "-R", known_host_name])
            if clear_exit_code != 0:
                raise typer.Exit(clear_exit_code)

    raise typer.Exit(
        _run_ssh_state(
            target_name,
            state_name,
            test_mode=False,
            state_output=state_output or DEFAULT_STATE_OUTPUT,
            state_verbose=state_verbose or DEFAULT_STATE_VERBOSE,
            observe=observe,
        )
    )


def main() -> None:
    internal_exit_code = _run_internal_subcommand()
    if internal_exit_code >= 0:
        raise SystemExit(internal_exit_code)

    application()


if __name__ == "__main__":
    main()
