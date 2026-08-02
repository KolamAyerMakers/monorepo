"""User-facing helper command."""

from __future__ import annotations

import json
import os
import pwd
import socket
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Protocol, TextIO, cast

import typer
from rich.console import Console, ConsoleOptions, RenderResult
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text

from maker_guide.chat.contract import (
    CHAT_INPUT_TOO_LONG_TEXT,
    DEFAULT_CHAT_MAX_INPUT_CHARS,
)
from maker_guide.config import (
    DEFAULT_CONFIG_PATH,
    load_bot_name,
    load_socket_path,
)
from maker_guide.llm_tutor import DEFAULT_TUTOR_TIMEOUT_SECONDS

try:
    import readline
except ImportError:
    readline = None

_HELP_SOCKET_TIMEOUT_SECONDS = DEFAULT_TUTOR_TIMEOUT_SECONDS + 2.0
_HELP_TIMEOUT_TEXT = "My remote brain is still thinking. Try me again in a moment."
_HELP_UNAVAILABLE_TEXT = "I can't reach my remote brain right now. Try me again in a moment."
_BAD_HELP_RESPONSE_TEXT = "My remote brain sent static. Try again in a moment."
_THINKING_BLOCK_WIDTH = 8
_THINKING_HOLD_START_FRAMES = 30
_THINKING_HOLD_END_FRAMES = 9
_THINKING_FRAMES_PER_SECOND = 25
_THINKING_BLOCK = "\u25a0"
_THINKING_DOT = "\u2b1d"
_THINKING_BASE_COLOR = (92, 156, 245)
_THINKING_BACKGROUND_COLOR = (10, 10, 10)
_THINKING_INACTIVE_ALPHA = 0.6
_THINKING_MIN_ALPHA = 0.3
_THINKING_TRAIL_ALPHAS = (1.0, 0.9, 0.65, 0.4225, 0.274625, 0.17850625)
_THINKING_TRAIL_BRIGHTNESS = (1.0, 1.15, 1.0, 1.0, 1.0, 1.0)
_THINKING_LABEL = " Thinking..."

_PASSTHROUGH_CONTEXT_SETTINGS = {
    "allow_extra_args": True,
    "allow_interspersed_args": False,
    "ignore_unknown_options": True,
}
app = typer.Typer(
    add_completion=False,
    help="Ask the Kolam Makers bot for CLI help.",
    pretty_exceptions_enable=False,
)
_RichConsole = Console


@dataclass(frozen=True, kw_only=True, slots=True)
class _HelpRuntime:
    """Shared state for one helper command invocation."""

    console: Console
    """Output console."""
    bot_name: str
    """Configured bot display name."""
    username: str
    """Current Unix username."""


@dataclass(frozen=True, kw_only=True, slots=True)
class _HelpInvocation:
    """Inputs for one helper command invocation."""

    message_parts: list[str]
    """Command-line message tokens passed after options."""
    input_stream: TextIO
    """Input stream for stdin or interactive reads."""
    console: Console
    """Console used to write responses."""
    bot_name: str
    """Configured bot display name."""
    socket_path: Path
    """Daemon socket path for help requests."""


class _ThinkingBlocks:
    def __init__(self) -> None:
        self.frame_number = 0

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        del console, options
        yield _render_thinking_blocks(self.frame_number)
        self.frame_number += 1


class _StreamingMarkdown:
    def __init__(self) -> None:
        self.chunks: list[str] = []
        self.frame_number = 0

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        del console, options
        if self.chunks:
            yield Markdown("".join(self.chunks))
            return
        yield _render_thinking_blocks(self.frame_number)
        self.frame_number += 1


class _SocketReader(Protocol):
    def recv(self, size: int, /) -> bytes:
        """Read bytes from a socket-like object."""
        ...


def main() -> None:
    """Run the helper command from command-line arguments."""
    app()


@app.command(context_settings=_PASSTHROUGH_CONTEXT_SETTINGS)
def ask(
    context: typer.Context,
    configuration_path: Annotated[
        Path,
        typer.Option("--config", help="Path to the daemon TOML configuration."),
    ] = DEFAULT_CONFIG_PATH,
) -> None:
    """Ask the bot for help with arguments, stdin, or an interactive prompt."""
    _run_help(
        _HelpInvocation(
            message_parts=context.args,
            input_stream=sys.stdin,
            console=Console(),
            bot_name=load_bot_name(configuration_path),
            socket_path=load_socket_path(configuration_path),
        ),
    )


def _run_help(help_invocation: _HelpInvocation) -> None:
    help_runtime = _HelpRuntime(
        console=help_invocation.console,
        bot_name=help_invocation.bot_name,
        username=_current_username(),
    )
    if help_invocation.message_parts:
        _write_chat_response(
            help_runtime,
            help_invocation.socket_path,
            " ".join(help_invocation.message_parts),
            False,
        )
        return
    if help_invocation.input_stream.isatty():
        _run_interactive_help(help_invocation.input_stream, help_runtime, help_invocation)
        return
    _write_chat_response(
        help_runtime,
        help_invocation.socket_path,
        help_invocation.input_stream.read(DEFAULT_CHAT_MAX_INPUT_CHARS + 1),
        False,
    )


def _run_interactive_help(
    input_stream: TextIO,
    help_runtime: _HelpRuntime,
    help_invocation: _HelpInvocation,
) -> None:
    help_runtime.console.out("guide is listening. Press Ctrl-D to exit.\n", end="")
    use_readline_prompt = input_stream is sys.stdin and help_runtime.console.is_terminal
    while True:
        line = _read_interactive_line(input_stream, help_runtime, use_readline_prompt)
        if line == "":
            help_runtime.console.out("\n", end="")
            return
        if not line.strip():
            continue
        if len(line) > DEFAULT_CHAT_MAX_INPUT_CHARS:
            if not use_readline_prompt:
                _drain_line(input_stream, line)
            if not help_runtime.console.is_terminal:
                help_runtime.console.out(line, end="")
            _write_bot_response(
                help_runtime.console,
                help_runtime.bot_name,
                CHAT_INPUT_TOO_LONG_TEXT,
                True,
            )
            continue
        if not help_runtime.console.is_terminal:
            help_runtime.console.out(line, end="")
        if _is_exit_command(line):
            return
        _write_chat_response(help_runtime, help_invocation.socket_path, line, True)


def _read_interactive_line(
    input_stream: TextIO,
    help_runtime: _HelpRuntime,
    use_readline_prompt: bool,
) -> str:
    prompt = f"{help_runtime.username}> "
    if not use_readline_prompt:
        help_runtime.console.out(prompt, end="")
        help_runtime.console.file.flush()
        return input_stream.readline(DEFAULT_CHAT_MAX_INPUT_CHARS + 1)
    try:
        line = input(prompt)
    except EOFError:
        return ""
    if readline is not None and line.strip():
        readline.add_history(line)
    return f"{line}\n"


def _write_chat_response(
    help_runtime: _HelpRuntime,
    socket_path: Path,
    message: str,
    show_message_prefix: bool,
) -> None:
    if len(message) > DEFAULT_CHAT_MAX_INPUT_CHARS:
        _write_bot_response(
            help_runtime.console,
            help_runtime.bot_name,
            CHAT_INPUT_TOO_LONG_TEXT,
            show_message_prefix,
        )
        return
    if help_runtime.console.is_terminal:
        _write_streamed_chat_response(
            help_runtime.console,
            help_runtime.bot_name,
            socket_path,
            message,
            show_message_prefix,
        )
        return
    _write_bot_response(
        help_runtime.console,
        help_runtime.bot_name,
        _send_help_request_with_animation(help_runtime.console, socket_path, message),
        show_message_prefix,
    )


def _write_streamed_chat_response(
    console: Console,
    bot_name: str,
    socket_path: Path,
    message: str,
    show_message_prefix: bool,
) -> None:
    if show_message_prefix:
        console.out(f"{bot_name}> ", end="")
    renderable = _StreamingMarkdown()

    def write_chunk(chunk: str) -> None:
        renderable.chunks.append(chunk)
        live.update(renderable, refresh=True)

    with Live(
        renderable,
        console=_truecolor_console(console),
        refresh_per_second=_THINKING_FRAMES_PER_SECOND,
        transient=True,
    ) as live:
        response = _send_help_request(
            socket_path,
            message,
            _terminal_name(),
            write_chunk,
        )
    _write_bot_response(console, bot_name, response, False)


def _send_help_request_with_animation(
    console: Console,
    socket_path: Path,
    message: str,
    chunk_writer: Callable[[str], None] | None = None,
) -> str:
    if chunk_writer is not None:
        return _send_help_request(socket_path, message, _terminal_name(), chunk_writer)
    if sys.stderr.isatty():
        animation_console = _RichConsole(file=sys.stderr, color_system="truecolor")
    elif console.is_terminal:
        animation_console = _truecolor_console(console)
    else:
        return _send_help_request(socket_path, message, _terminal_name())
    with Live(
        _ThinkingBlocks(),
        console=animation_console,
        refresh_per_second=_THINKING_FRAMES_PER_SECOND,
        transient=True,
    ):
        return _send_help_request(socket_path, message, _terminal_name())


def _send_help_request(
    socket_path: Path,
    message: str,
    terminal: str | None,
    chunk_writer: Callable[[str], None] | None = None,
) -> str:
    payload = (
        json.dumps(
            {
                "version": 1,
                "kind": "help",
                "text": message,
                "terminal": terminal,
                "ssh_connection": os.environ.get("SSH_CONNECTION"),
                "stream": chunk_writer is not None,
            },
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client_socket:
            client_socket.settimeout(_HELP_SOCKET_TIMEOUT_SECONDS)
            client_socket.connect(str(socket_path))
            client_socket.sendall(payload)
            return _read_help_response(client_socket, chunk_writer)
    except TimeoutError:
        return _HELP_TIMEOUT_TEXT
    except OSError:
        return _HELP_UNAVAILABLE_TEXT


def _render_thinking_blocks(frame_number: int) -> Text:
    text = Text()
    for position in range(_THINKING_BLOCK_WIDTH):
        color_index = _thinking_color_index(frame_number, position)
        if 0 <= color_index < len(_THINKING_TRAIL_ALPHAS):
            text.append(_THINKING_BLOCK, style=_thinking_trail_color(color_index))
        else:
            text.append(_THINKING_DOT, style=_thinking_inactive_color(frame_number))
    text.append(_THINKING_LABEL, style=_thinking_trail_color(0))
    return text


def _thinking_color_index(frame_number: int, position: int) -> int:
    active_position, is_holding, hold_progress, _, _, _, is_moving_forward = (
        _thinking_scanner_state(frame_number)
    )
    directional_distance = (
        active_position - position if is_moving_forward else position - active_position
    )
    if is_holding:
        return directional_distance + hold_progress
    if directional_distance == 0:
        return 0
    if 0 < directional_distance < len(_THINKING_TRAIL_ALPHAS):
        return directional_distance
    return -1


def _thinking_scanner_state(
    frame_number: int,
) -> tuple[int, bool, int, int, int, int, bool]:
    backward_frames = _THINKING_BLOCK_WIDTH - 1
    total_frames = (
        _THINKING_BLOCK_WIDTH
        + _THINKING_HOLD_END_FRAMES
        + backward_frames
        + _THINKING_HOLD_START_FRAMES
    )
    frame_index = frame_number % total_frames
    if frame_index < _THINKING_BLOCK_WIDTH:
        return frame_index, False, 0, 0, frame_index, _THINKING_BLOCK_WIDTH, True
    if frame_index < _THINKING_BLOCK_WIDTH + _THINKING_HOLD_END_FRAMES:
        return (
            _THINKING_BLOCK_WIDTH - 1,
            True,
            frame_index - _THINKING_BLOCK_WIDTH,
            _THINKING_HOLD_END_FRAMES,
            0,
            0,
            True,
        )
    if frame_index < _THINKING_BLOCK_WIDTH + _THINKING_HOLD_END_FRAMES + backward_frames:
        backward_index = frame_index - _THINKING_BLOCK_WIDTH - _THINKING_HOLD_END_FRAMES
        return (
            _THINKING_BLOCK_WIDTH - 2 - backward_index,
            False,
            0,
            0,
            backward_index,
            backward_frames,
            False,
        )
    return (
        0,
        True,
        frame_index - _THINKING_BLOCK_WIDTH - _THINKING_HOLD_END_FRAMES - backward_frames,
        _THINKING_HOLD_START_FRAMES,
        0,
        0,
        False,
    )


def _thinking_trail_color(color_index: int) -> str:
    return _thinking_alpha_color(
        min(_THINKING_BASE_COLOR[0] * _THINKING_TRAIL_BRIGHTNESS[color_index], 255),
        min(_THINKING_BASE_COLOR[1] * _THINKING_TRAIL_BRIGHTNESS[color_index], 255),
        min(_THINKING_BASE_COLOR[2] * _THINKING_TRAIL_BRIGHTNESS[color_index], 255),
        _THINKING_TRAIL_ALPHAS[color_index],
    )


def _thinking_inactive_color(frame_number: int) -> str:
    (
        _,
        is_holding,
        hold_progress,
        hold_total,
        movement_progress,
        movement_total,
        _,
    ) = _thinking_scanner_state(frame_number)
    fade_factor = 1.0
    if is_holding and hold_total > 0:
        fade_factor = max(
            _THINKING_MIN_ALPHA,
            1 - hold_progress / hold_total * (1 - _THINKING_MIN_ALPHA),
        )
    elif movement_total > 0:
        fade_factor = _THINKING_MIN_ALPHA + movement_progress / max(1, movement_total - 1) * (
            1 - _THINKING_MIN_ALPHA
        )
    return _thinking_alpha_color(
        _THINKING_BASE_COLOR[0],
        _THINKING_BASE_COLOR[1],
        _THINKING_BASE_COLOR[2],
        _THINKING_INACTIVE_ALPHA * fade_factor,
    )


def _truecolor_console(console: Console) -> Console:
    if console.color_system == "truecolor":
        return console
    return _RichConsole(
        file=console.file,
        force_terminal=console.is_terminal,
        color_system="truecolor",
    )


def _thinking_alpha_color(red: float, green: float, blue: float, alpha: float) -> str:
    return "#" + "".join(
        f"{round(background + (foreground - background) * alpha):02x}"
        for foreground, background in zip(
            (red, green, blue),
            _THINKING_BACKGROUND_COLOR,
            strict=True,
        )
    )


def _help_response_text(response: bytes) -> str:
    try:
        loaded = cast("object", json.loads(response.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _BAD_HELP_RESPONSE_TEXT
    if not isinstance(loaded, dict):
        return _BAD_HELP_RESPONSE_TEXT
    response_object = cast("dict[object, object]", loaded)
    if response_object.get("ok") is not True:
        error = (
            response_object.get("error")
            if isinstance(response_object.get("error"), str)
            else "bad response"
        )
        return f"My wires crossed: {error}"
    text = response_object.get("text")
    if not isinstance(text, str):
        return _BAD_HELP_RESPONSE_TEXT
    return text


def _read_help_response(
    client_socket: _SocketReader,
    chunk_writer: Callable[[str], None] | None,
) -> str:
    buffered = b""
    while True:
        received = client_socket.recv(4096)
        if received == b"":
            break
        buffered += received
        while b"\n" in buffered:
            response_line, buffered = buffered.split(b"\n", 1)
            response_text = _handle_help_response_line(response_line, chunk_writer)
            if response_text is not None:
                return response_text
    if buffered:
        response_text = _handle_help_response_line(buffered, chunk_writer)
        if response_text is not None:
            return response_text
    return _BAD_HELP_RESPONSE_TEXT


def _handle_help_response_line(
    response: bytes,
    chunk_writer: Callable[[str], None] | None,
) -> str | None:
    if chunk_writer is None:
        return _help_response_text(response)
    try:
        loaded = cast("object", json.loads(response.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _BAD_HELP_RESPONSE_TEXT
    if not isinstance(loaded, dict):
        return _BAD_HELP_RESPONSE_TEXT
    response_object = cast("dict[object, object]", loaded)
    chunk = response_object.get("chunk")
    if isinstance(chunk, str):
        chunk_writer(chunk)
        return None
    return _help_response_text(response)


def _write_bot_response(
    console: Console,
    bot_name: str,
    message: str,
    show_message_prefix: bool,
) -> None:
    if message == "":
        return
    if show_message_prefix:
        console.out(f"{bot_name}> ", end="")
    if console.is_terminal:
        console.print(Markdown(message))
        return
    console.out(message, end="")
    if not message.endswith("\n"):
        console.out("\n", end="")


def _drain_line(input_stream: TextIO, line: str) -> None:
    if line.endswith("\n"):
        return
    while True:
        remainder = input_stream.readline(DEFAULT_CHAT_MAX_INPUT_CHARS + 1)
        if remainder == "" or remainder.endswith("\n"):
            return


def _current_username() -> str:
    return pwd.getpwuid(os.getuid()).pw_name


def _terminal_name() -> str | None:
    try:
        return os.ttyname(0)
    except OSError:
        return None


def _is_exit_command(line: str) -> bool:
    return line.strip().casefold() in {"exit", "quit"}
