"""Command-line client used by Bash hooks."""

from __future__ import annotations

import json
import os
import socket
import sys
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated, cast

import typer
from rich.console import Console

DEFAULT_SOCKET_PATH = Path("/run/maker-guide/preexec.sock")
DEFAULT_TIMEOUT_SECONDS = 0.02
_HOOK_SOCKET_EXCEPTIONS = (OSError, TimeoutError, ValueError)


HookSender = Callable[[Path, float, dict[str, object]], None]
_PASSTHROUGH_CONTEXT_SETTINGS = {
    "allow_extra_args": True,
    "allow_interspersed_args": False,
    "ignore_unknown_options": True,
}
app = typer.Typer(
    add_completion=False,
    help="Send Bash hook events to maker-guide.",
    pretty_exceptions_enable=False,
)


class HookShell(StrEnum):
    """Supported shell initialization targets."""

    bash = "bash"


@dataclass(frozen=True, kw_only=True, slots=True)
class HookCommandDependencies:
    """Dependencies injected into hook command execution."""

    sender: HookSender | None = None
    """Sender used instead of the Unix socket transport."""

    program_name: str = "maker-guide-bash-hook"
    """Command name embedded in generated shell initialization code."""


@dataclass(frozen=True, kw_only=True, slots=True)
class HookCommandOptions:
    """Parsed hook command options and dependencies."""

    socket_path: Path
    """Unix socket path used to send hook events."""

    timeout_seconds: float
    """Maximum socket send time before failing open."""

    sender: HookSender | None
    """Sender used instead of the Unix socket transport."""

    program_name: str
    """Command name embedded in generated shell initialization code."""


def main() -> None:
    """Run the Bash hook CLI."""
    app(obj=HookCommandDependencies(program_name=sys.argv[0]))


def run(
    arguments: Sequence[str] | None = None,
    sender: HookSender | None = None,
    program_name: str | None = None,
) -> int:
    """Run the Typer app and return the shell-facing exit status."""
    result = cast(
        "object",
        app(
            args=list(arguments) if arguments is not None else None,
            standalone_mode=False,
            obj=HookCommandDependencies(
                sender=sender,
                program_name=program_name or "maker-guide-bash-hook",
            ),
        ),
    )
    if isinstance(result, int):
        return result
    return 0


@app.callback()
def configure(
    context: typer.Context,
    socket_path: Annotated[
        Path,
        typer.Option("--socket", help="Path to the daemon Unix socket."),
    ] = DEFAULT_SOCKET_PATH,
    timeout_seconds: Annotated[
        float,
        typer.Option("--timeout", min=0.001, help="Socket send timeout in seconds."),
    ] = DEFAULT_TIMEOUT_SECONDS,
) -> None:
    """Configure shared hook command options."""
    dependencies = _dependencies_from_context(context)
    context.obj = HookCommandOptions(
        socket_path=socket_path,
        timeout_seconds=timeout_seconds,
        sender=dependencies.sender,
        program_name=dependencies.program_name,
    )


@app.command()
def init(
    context: typer.Context,
    shell: Annotated[HookShell, typer.Argument(help="Shell to initialize.")],
) -> None:
    """Print shell initialization code."""
    Console().out(render_shell_init(shell, _options_from_context(context).program_name), end="")


@app.command(context_settings=_PASSTHROUGH_CONTEXT_SETTINGS)
def before(context: typer.Context) -> None:
    """Send a pre-command event."""
    _send_payload_from_options(
        _options_from_context(context),
        _payload_from_arguments("before", tuple(context.args), None),
    )


@app.command(context_settings=_PASSTHROUGH_CONTEXT_SETTINGS)
def after(
    context: typer.Context,
    exit_status: Annotated[
        int,
        typer.Argument(min=0, max=255, help="Completed command exit status."),
    ],
) -> None:
    """Send a post-command event."""
    _send_payload_from_options(
        _options_from_context(context),
        _payload_from_arguments("after", tuple(context.args), exit_status),
        response_requested=True,
    )


def send_hook_event(
    socket_path: Path,
    timeout_seconds: float,
    payload: dict[str, object],
    *,
    response_requested: bool = False,
) -> None:
    """Send a hook event, optionally waiting for the daemon acknowledgement."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client_socket:
            client_socket.settimeout(timeout_seconds)
            client_socket.connect(str(socket_path))
            client_socket.sendall(_encode_payload(payload, response_requested=response_requested))
            if response_requested:
                client_socket.recv(1)
    except _HOOK_SOCKET_EXCEPTIONS:
        return


def render_bash_init(program_name: str = "maker-guide-bash-hook") -> str:
    """Return Bash integration code suitable for eval."""
    _hook_template = r"""
if ! declare -p preexec_functions &>/dev/null 2>&1; then
    declare -a preexec_functions
fi
if ! declare -p precmd_functions &>/dev/null 2>&1; then
    declare -a precmd_functions
fi

__MAKER_GUIDE_LAST_COMMAND=

__maker_guide_fire_and_forget() {
    ( "$@" >/dev/null 2>&1 & )
}

__maker_guide_preexec() {
    local command="${BASH_COMMAND:-}"
    local full_command="${1:-}"
    if [[ -n "$full_command" && ( -z "$command" || "$full_command" == "$command"* ) ]]; then
        command=$full_command
    fi
    [[ -z "$__MAKER_GUIDE_LAST_COMMAND" ]] || return 0
    [[ -n "$command" ]] || return 0
    __MAKER_GUIDE_LAST_COMMAND=$command
    __maker_guide_fire_and_forget __MAKER_GUIDE_HOOK before "$command"
}

__maker_guide_precmd() {
    local last_status=$?
    [[ -n "$__MAKER_GUIDE_LAST_COMMAND" ]] || return 0
    __MAKER_GUIDE_HOOK after "$last_status" "$__MAKER_GUIDE_LAST_COMMAND" >/dev/null 2>&1
    __MAKER_GUIDE_LAST_COMMAND=
}

__maker_guide_remove_existing_preexec() {
    local hook_function
    local remaining_functions=()
    for hook_function in "${preexec_functions[@]:-}"; do
        [[ "$hook_function" == "__maker_guide_preexec" ]] || remaining_functions+=("$hook_function")
    done
    preexec_functions=("${remaining_functions[@]}")
}

__maker_guide_remove_existing_precmd() {
    local hook_function
    local remaining_functions=()
    for hook_function in "${precmd_functions[@]:-}"; do
        [[ "$hook_function" == "__maker_guide_precmd" ]] || remaining_functions+=("$hook_function")
    done
    precmd_functions=("${remaining_functions[@]}")
}

___maker_guide_load_bash_preexec() {
_BASH_PREEXEC_SOURCE_
}
___maker_guide_load_bash_preexec
unset -f ___maker_guide_load_bash_preexec

if declare -f __bp_hook_preexec_into_debug >/dev/null 2>&1; then
    __bp_hook_preexec_proc=__bp_hook_preexec_into_debug
fi

__maker_guide_remove_existing_preexec
__maker_guide_remove_existing_precmd
unset -f __maker_guide_remove_existing_preexec __maker_guide_remove_existing_precmd

preexec_functions+=(__maker_guide_preexec)
precmd_functions+=(__maker_guide_precmd)
"""
    return (
        _hook_template.replace("__MAKER_GUIDE_HOOK", program_name)
        .replace("_BASH_PREEXEC_SOURCE_", _bash_preexec_source())
        .lstrip()
    )


def render_shell_init(shell: HookShell, program_name: str = "maker-guide-bash-hook") -> str:
    """Return shell integration code suitable for eval."""
    if shell == HookShell.bash:
        return render_bash_init(program_name)
    raise ValueError(f"unsupported shell: {shell}")


def _payload_from_arguments(
    phase: str,
    command_parts: Sequence[str],
    exit_status: int | None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "event_id": str(uuid.uuid4()),
        "version": 1,
        "type": "preexec" if phase == "before" else "postexec",
        "cwd": str(Path.cwd()),
        "command": _command_from_parts(command_parts),
        "shell": "bash",
        "tty": _tty_name(),
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    if phase == "after":
        payload["exit_status"] = exit_status
    if (ssh_auth_method := _ssh_auth_method()) is not None:
        payload["ssh_auth_method"] = ssh_auth_method
    return payload


def _send_payload_from_options(
    options: HookCommandOptions,
    payload: dict[str, object],
    *,
    response_requested: bool = False,
) -> None:
    if options.sender is not None:
        options.sender(options.socket_path, options.timeout_seconds, payload)
        return
    send_hook_event(
        options.socket_path,
        options.timeout_seconds,
        payload,
        response_requested=response_requested,
    )


def _dependencies_from_context(context: typer.Context) -> HookCommandDependencies:
    context_object = cast("object", context.obj)
    if isinstance(context_object, HookCommandDependencies):
        return context_object
    return HookCommandDependencies()


def _options_from_context(context: typer.Context) -> HookCommandOptions:
    context_object = cast("object", context.obj)
    if isinstance(context_object, HookCommandOptions):
        return context_object
    raise RuntimeError("hook command options were not initialized")


def _encode_payload(payload: dict[str, object], *, response_requested: bool = False) -> bytes:
    return (
        json.dumps(payload | {"reply": response_requested}, separators=(",", ":")).encode("utf-8")
        + b"\n"
    )


def _bash_preexec_source() -> str:
    from importlib.resources import files  # noqa: PLC0415

    return files("maker_guide").joinpath("bash-preexec.sh").read_text(encoding="utf-8")


def _command_from_parts(parts: Sequence[str]) -> str:
    if len(parts) == 1:
        return parts[0]
    return " ".join(parts)


def _tty_name() -> str | None:
    try:
        return os.ttyname(0)
    except OSError:
        return None


def _ssh_auth_method() -> str | None:
    """Return only the sshd authentication method, never auth-info contents."""
    authentication_path = os.environ.get("SSH_USER_AUTH")
    if authentication_path is None:
        return None
    try:
        authentication_details = Path(authentication_path).read_text(encoding="utf-8")
        authentication_method = authentication_details.split(maxsplit=1)[0]
    except (IndexError, OSError, UnicodeDecodeError):
        return None
    return authentication_method if authentication_method in {"publickey", "password"} else None
