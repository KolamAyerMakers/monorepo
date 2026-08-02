"""Tests for the user-facing helper command."""

from __future__ import annotations

import builtins
import io
import sqlite3
import sys
from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace
from typing import Self, TextIO, cast, override

import pytest
from rich.console import Console

import maker_guide.cli.help as help_cli
from maker_guide.chat.contract import CHAT_INPUT_TOO_LONG_TEXT
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.repositories.cohort_membership import CohortMembership, upsert_membership
from maker_guide.repositories.course_release import CourseRelease, upsert_course_release
from maker_guide.repositories.help_interaction import list_recent_help_interactions
from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.learner import Learner, upsert_learner

FREEFORM_TUTOR_DISABLED_TEXT = (
    dedent(
        """\
    I can't do open-ended tutoring here yet. Run `guide now` for your current quest,
    `guide check` when you've tried it, or `guide answer 'your answer'` when the
    quest asks a question.
    """,
    )
    .replace("\n", " ")
    .strip()
)


class InteractiveInput(io.StringIO):
    """String stream that behaves like a terminal for mode detection."""

    @override
    def isatty(self) -> bool:
        """Report terminal mode."""
        return True


class BoundedReadInput(io.StringIO):
    """String stream that records requested read sizes."""

    def __init__(self, value: str) -> None:
        super().__init__(value)
        self.read_sizes: list[int] = []

    @override
    def read(self, size: int | None = -1) -> str:
        if size is not None:
            self.read_sizes.append(size)
        return super().read(size)


class TerminalOutput(io.StringIO):
    """String stream that behaves like a terminal for animation routing."""

    @override
    def isatty(self) -> bool:
        """Report terminal mode."""
        return True


def _write_configuration(
    temporary_path: Path,
    database_path: Path,
    nickname: str = "guide",
) -> Path:
    password_path = temporary_path / "irc-password.txt"
    password_path.write_text("secret", encoding="utf-8")
    configuration_path = temporary_path / "config.toml"
    configuration_path.write_text(
        f"""
        [socket]
        path = "{temporary_path / "maker-guide.sock"}"

        [database]
        path = "{database_path}"

        [irc]
        server = "irc.example"
        nickname = "{nickname}"
        username = "{nickname}"
        channels = ["#kolam"]

        [irc.sasl]
        username = "{nickname}"
        password_file = "{password_path}"
        """,
        encoding="utf-8",
    )
    return configuration_path


def _write_configuration_with_missing_password_env(
    temporary_path: Path,
    database_path: Path,
) -> Path:
    configuration_path = temporary_path / "config.toml"
    configuration_path.write_text(
        f"""
        [socket]
        path = "{temporary_path / "maker-guide.sock"}"

        [database]
        path = "{database_path}"

        [irc]
        server = "irc.example"
        nickname = "guide"
        username = "guide"
        channels = ["#kolam"]

        [irc.sasl]
        username = "guide"
        password_env = "MAKER_GUIDE_IRC_PASSWORD"
        """,
        encoding="utf-8",
    )
    return configuration_path


def _write_tutor_configuration(
    temporary_path: Path,
    database_path: Path,
) -> Path:
    configuration_path = _write_configuration(temporary_path, database_path)
    api_key_path = temporary_path / "openrouter-api-key"
    api_key_path.write_text("sk-or-test\n", encoding="utf-8")
    with configuration_path.open("a", encoding="utf-8") as configuration_file:
        configuration_file.write(
            f"""

            [llm_tutor]
            enabled = true
            api_key_file = "{api_key_path}"
            """,
        )
    return configuration_path


def _run_command(
    monkeypatch: pytest.MonkeyPatch,
    arguments: list[str],
    input_stream: TextIO | None = None,
    daemon_response: str | None = FREEFORM_TUTOR_DISABLED_TEXT,
    *,
    force_terminal: bool = False,
) -> str:
    output, exit_code = _run_command_with_exit(
        monkeypatch,
        arguments,
        input_stream,
        daemon_response,
        force_terminal=force_terminal,
    )
    assert exit_code == 0
    return output


def _run_command_with_exit(
    monkeypatch: pytest.MonkeyPatch,
    arguments: list[str],
    input_stream: TextIO | None = None,
    daemon_response: str | None = FREEFORM_TUTOR_DISABLED_TEXT,
    *,
    force_terminal: bool = False,
) -> tuple[str, int | str | None]:
    output_stream = io.StringIO()
    if force_terminal:

        def silent_live(
            renderable: object,
            *,
            console: Console,
            refresh_per_second: int,
            transient: bool,
        ) -> AbstractContextManager[None]:
            del renderable, console, refresh_per_second, transient
            return nullcontext()

        def console() -> Console:
            return Console(file=output_stream, force_terminal=True, color_system=None, width=80)

        monkeypatch.setattr(help_cli, "Console", console)
        monkeypatch.setattr(help_cli, "Live", silent_live)
    if daemon_response is not None:

        def send_help_request(
            _socket_path: Path,
            _message: str,
            _terminal: str | None,
            _chunk_writer: object = None,
        ) -> str:
            return daemon_response

        monkeypatch.setattr(
            help_cli,
            "_send_help_request",
            send_help_request,
        )
    monkeypatch.setattr(sys, "argv", ["guide", *arguments])
    monkeypatch.setattr(sys, "stdin", input_stream or io.StringIO())
    monkeypatch.setattr(sys, "stdout", output_stream)
    with pytest.raises(SystemExit) as system_exit:
        help_cli.main()
    return output_stream.getvalue(), system_exit.value.code


def test_help_writes_argument_message_without_prefix(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Command arguments are treated as one non-interactive free-form message."""
    _set_os_username(monkeypatch, "alice")
    _write_learner(migrated_database_path)

    assert (
        _run_command(
            monkeypatch,
            [
                "--config",
                str(_write_configuration(tmp_path, migrated_database_path)),
                "explain",
                "chmod",
                "755",
            ],
        )
        == f"{FREEFORM_TUTOR_DISABLED_TEXT}\n"
    )


def test_terminal_response_renders_markdown(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Terminal help output renders Markdown instead of showing raw markers."""
    _set_os_username(monkeypatch, "alice")

    assert (
        _run_command(
            monkeypatch,
            [
                "--config",
                str(_write_configuration(tmp_path, migrated_database_path)),
                "hello",
            ],
            daemon_response="Start **bold** now",
            force_terminal=True,
        ).strip()
        == "Start bold now"
    )


def test_terminal_help_uses_thinking_animation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Terminal help wraps daemon waits in the block animation."""
    live_calls: list[tuple[object, Console, int, bool]] = []

    def recording_live(
        renderable: object,
        *,
        console: Console,
        refresh_per_second: int,
        transient: bool,
    ) -> AbstractContextManager[None]:
        live_calls.append((renderable, console, refresh_per_second, transient))
        return nullcontext()

    def send_help_request(socket_path: Path, message: str, terminal: str | None) -> str:
        assert socket_path == tmp_path / "maker-guide.sock"
        assert message == "hello"
        assert terminal is None
        return "daemon response"

    monkeypatch.setattr(help_cli, "Live", recording_live)
    monkeypatch.setattr(help_cli, "_send_help_request", send_help_request)
    error_stream = TerminalOutput()
    monkeypatch.setattr(sys, "stderr", error_stream)
    console = Console(file=io.StringIO(), force_terminal=False, color_system=None)

    assert (
        help_cli._send_help_request_with_animation(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            console,
            tmp_path / "maker-guide.sock",
            "hello",
        )
        == "daemon response"
    )
    assert len(live_calls) == 1
    renderable, live_console, refresh_per_second, transient = live_calls[0]
    assert isinstance(renderable, help_cli._ThinkingBlocks)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert live_console.file is error_stream
    assert refresh_per_second == 25
    assert transient is True


def test_thinking_blocks_match_requested_shape() -> None:
    """The thinking renderer uses opencode's eight block scanner."""
    assert (
        help_cli._render_thinking_blocks(0).plain  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        == "\u25a0\u2b1d\u2b1d\u2b1d\u2b1d\u2b1d\u2b1d\u2b1d Thinking..."
    )
    assert (
        help_cli._render_thinking_blocks(7).plain  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        == "\u2b1d\u2b1d\u25a0\u25a0\u25a0\u25a0\u25a0\u25a0 Thinking..."
    )


def test_thinking_blocks_use_opencode_colors() -> None:
    """The block colors follow opencode's derived trail and inactive fade."""
    assert help_cli._thinking_trail_color(0) == "#5c9cf5"  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert help_cli._thinking_trail_color(1) == "#60a2e6"  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert help_cli._thinking_trail_color(2) == "#3f69a3"  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert help_cli._thinking_inactive_color(0) == "#192434"  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert help_cli._thinking_inactive_color(7) == "#3b6297"  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001


def test_help_response_reader_streams_chunks_before_final_text() -> None:
    """Socket JSONL chunks are written as they arrive."""
    chunks: list[str] = []
    client_socket = _ChunkedSocket(
        b"".join(
            (
                b'{"ok":true,"chunk":"hello "}\n',
                b'{"ok":true,"chunk":"there"}\n',
                b'{"ok":true,"execute":true,"text":"hello there"}\n',
            ),
        ),
    )

    assert help_cli._read_help_response(client_socket, chunks.append) == "hello there"  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert chunks == ["hello ", "there"]


def test_terminal_chat_response_requests_streaming(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Terminal CLI help streams through Live and prints final Markdown."""
    output_stream = io.StringIO()
    chunk_writers: list[Callable[[str], None] | None] = []
    initial_renders: list[str] = []
    live_updates: list[str] = []

    class _RecordingLive:
        def __init__(
            self,
            renderable: object,
            *,
            console: Console,
            refresh_per_second: int,
            transient: bool,
        ) -> None:
            assert refresh_per_second == 25
            assert transient is True
            self.renderable = cast("help_cli._StreamingMarkdown", renderable)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            self.console = console

        def __enter__(self) -> Self:
            del self.console
            initial_renders.append(
                help_cli._render_thinking_blocks(self.renderable.frame_number).plain,  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            )
            return self

        def __exit__(
            self,
            exception_type: type[BaseException] | None,
            exception: BaseException | None,
            traceback: object,
        ) -> None:
            del exception_type, exception, traceback

        def update(self, renderable: object, *, refresh: bool) -> None:
            assert refresh is True
            live_updates.append("".join(cast("help_cli._StreamingMarkdown", renderable).chunks))  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

    def send_help_request(
        socket_path: Path,
        message: str,
        terminal: str | None,
        chunk_writer: Callable[[str], None] | None = None,
    ) -> str:
        assert socket_path == tmp_path / "maker-guide.sock"
        assert message == "hello"
        assert terminal is None
        chunk_writers.append(chunk_writer)
        assert chunk_writer is not None
        chunk_writer("Start **bold")
        chunk_writer("** now")
        return "Start **bold** now"

    monkeypatch.setattr(help_cli, "Live", _RecordingLive)
    monkeypatch.setattr(help_cli, "_send_help_request", send_help_request)
    help_cli._write_chat_response(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        help_cli._HelpRuntime(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            console=Console(file=output_stream, force_terminal=True, color_system=None),
            bot_name="guide",
            username="alice",
        ),
        tmp_path / "maker-guide.sock",
        "hello",
        True,
    )

    assert len(chunk_writers) == 1
    assert initial_renders == ["\u25a0\u2b1d\u2b1d\u2b1d\u2b1d\u2b1d\u2b1d\u2b1d Thinking..."]
    assert live_updates == ["Start **bold", "Start **bold** now"]
    assert output_stream.getvalue().rstrip() == "guide> Start bold now"


class _ChunkedSocket:
    def __init__(self, response: bytes) -> None:
        self._response = response

    def recv(self, size: int) -> bytes:
        response = self._response[:size]
        self._response = self._response[size:]
        return response


def test_help_rejects_oversized_argument_message(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Oversized argument input is rejected before help interaction storage."""
    _set_os_username(monkeypatch, "alice")
    monkeypatch.setattr(help_cli, "DEFAULT_CHAT_MAX_INPUT_CHARS", 8)
    _write_learner(migrated_database_path)

    assert (
        _run_command(
            monkeypatch,
            [
                "--config",
                str(_write_configuration(tmp_path, migrated_database_path)),
                "x" * 9,
            ],
        )
        == f"{CHAT_INPUT_TOO_LONG_TEXT}\n"
    )
    with connect_database(migrated_database_path) as database_connection:
        assert list_recent_help_interactions(database_connection, "alice", 10) == []


def test_help_does_not_require_irc_password_env(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The helper needs the bot name, not daemon IRC credentials."""
    monkeypatch.delenv("MAKER_GUIDE_IRC_PASSWORD", raising=False)
    _set_os_username(monkeypatch, "alice")
    _write_learner(migrated_database_path)

    assert (
        _run_command(
            monkeypatch,
            [
                "--config",
                str(
                    _write_configuration_with_missing_password_env(
                        tmp_path,
                        migrated_database_path,
                    ),
                ),
                "hello",
            ],
        )
        == f"{FREEFORM_TUTOR_DISABLED_TEXT}\n"
    )


def test_help_tutor_uses_daemon_socket_without_provider_environment(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tutor-enabled CLI help does not construct a provider client in the user process."""
    _set_os_username(monkeypatch, "alice")
    socket_calls: list[tuple[Path, str, str | None]] = []

    def send_help_request(socket_path: Path, message: str, terminal: str | None) -> str:
        socket_calls.append((socket_path, message, terminal))
        return "daemon tutor response"

    monkeypatch.setattr(help_cli, "_send_help_request", send_help_request)

    assert (
        _run_command(
            monkeypatch,
            [
                "--config",
                str(_write_tutor_configuration(tmp_path, migrated_database_path)),
                "hello",
            ],
            daemon_response=None,
        )
        == "daemon tutor response\n"
    )
    assert socket_calls == [(tmp_path / "maker-guide.sock", "hello", None)]


def test_help_writes_pipeline_input_without_prefix(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pipeline input is handled without interactive prompts or prefixes."""
    _set_os_username(monkeypatch, "alice")
    _write_learner(migrated_database_path)

    assert (
        _run_command(
            monkeypatch,
            ["--config", str(_write_configuration(tmp_path, migrated_database_path))],
            io.StringIO("make failed\nexit status 2\n"),
        )
        == f"{FREEFORM_TUTOR_DISABLED_TEXT}\n"
    )


def test_help_reads_pipeline_input_with_size_bound(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pipeline input is bounded before dispatch to shared chat handling."""
    _set_os_username(monkeypatch, "alice")
    monkeypatch.setattr(help_cli, "DEFAULT_CHAT_MAX_INPUT_CHARS", 8)
    _write_learner(migrated_database_path)
    input_stream = BoundedReadInput("x" * 10)

    assert (
        _run_command(
            monkeypatch,
            ["--config", str(_write_configuration(tmp_path, migrated_database_path))],
            input_stream,
        )
        == f"{CHAT_INPUT_TOO_LONG_TEXT}\n"
    )
    assert input_stream.read_sizes == [9]
    with connect_database(migrated_database_path) as database_connection:
        assert list_recent_help_interactions(database_connection, "alice", 10) == []


def test_help_guides_interactive_freeform_input(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Terminal input gets a simple prompt loop with free-form guidance."""
    _set_os_username(monkeypatch, "alice")
    _write_learner(migrated_database_path)

    assert _run_command(
        monkeypatch,
        ["--config", str(_write_configuration(tmp_path, migrated_database_path))],
        InteractiveInput("explain ls\n"),
    ) == (
        "guide is listening. Press Ctrl-D to exit.\n"
        "alice> explain ls\n"
        f"guide> {FREEFORM_TUTOR_DISABLED_TEXT}\n"
        "alice> \n"
    )


def test_help_ignores_blank_interactive_input(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Blank interactive input shows the next prompt without calling the daemon."""
    _set_os_username(monkeypatch, "alice")
    _write_learner(migrated_database_path)
    daemon_messages: list[str] = []

    def send_help_request(
        _socket_path: Path,
        message: str,
        _terminal: str | None,
        _chunk_writer: object = None,
    ) -> str:
        daemon_messages.append(message)
        return "daemon response"

    monkeypatch.setattr(help_cli, "_send_help_request", send_help_request)

    assert (
        _run_command(
            monkeypatch,
            ["--config", str(_write_configuration(tmp_path, migrated_database_path))],
            InteractiveInput("\nquit\n"),
            daemon_response=None,
        )
        == "guide is listening. Press Ctrl-D to exit.\nalice> alice> quit\n"
    )
    assert daemon_messages == []


def test_help_interactive_terminal_uses_readline_history(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Real terminal input gets stdlib readline editing and in-session history."""
    _set_os_username(monkeypatch, "alice")
    _write_learner(migrated_database_path)
    readline_history: list[str] = []
    input_lines = iter(("explain ls",))

    def terminal_input(prompt: str = "") -> str:
        sys.stdout.write(prompt)
        try:
            return next(input_lines)
        except StopIteration as stop_iteration:
            raise EOFError from stop_iteration

    monkeypatch.setattr(
        help_cli,
        "readline",
        SimpleNamespace(add_history=readline_history.append),
    )
    monkeypatch.setattr(builtins, "input", terminal_input)

    output = _run_command(
        monkeypatch,
        ["--config", str(_write_configuration(tmp_path, migrated_database_path))],
        InteractiveInput(""),
        daemon_response="ok",
        force_terminal=True,
    )

    assert output.startswith("guide is listening. Press Ctrl-D to exit.\nalice> guide> ok")
    assert output.endswith("alice> \n")
    assert readline_history == ["explain ls"]


def test_help_rejects_oversized_interactive_input_and_continues(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Interactive oversized input is rejected without ending the prompt loop."""
    _set_os_username(monkeypatch, "alice")
    monkeypatch.setattr(help_cli, "DEFAULT_CHAT_MAX_INPUT_CHARS", 8)
    _write_learner(migrated_database_path)

    assert _run_command(
        monkeypatch,
        ["--config", str(_write_configuration(tmp_path, migrated_database_path))],
        InteractiveInput(f"{'x' * 9}\nquit\n"),
    ) == (
        "guide is listening. Press Ctrl-D to exit.\n"
        f"alice> {'x' * 9}"
        f"guide> {CHAT_INPUT_TOO_LONG_TEXT}\n"
        "alice> quit\n"
    )
    with connect_database(migrated_database_path) as database_connection:
        assert list_recent_help_interactions(database_connection, "alice", 10) == []


@pytest.mark.parametrize("exit_command", [" EXIT \n", "quit\n"])
def test_help_exits_interactive_input(
    exit_command: str,
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exit commands stop the interactive loop without a bot response."""
    _set_os_username(monkeypatch, "alice")
    with connect_database(migrated_database_path) as database_connection:
        upsert_learner(
            database_connection,
            Learner(
                handle="alice",
                joined_at="2026-07-18T09:00:00Z",
                tagline=None,
                created_at="2026-07-18T09:00:00Z",
            ),
        )

    assert (
        _run_command(
            monkeypatch,
            ["--config", str(_write_configuration(tmp_path, migrated_database_path))],
            InteractiveInput(exit_command),
        )
        == f"guide is listening. Press Ctrl-D to exit.\nalice> {exit_command}"
    )


def test_help_requires_configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Help uses the configured IRC nickname instead of inventing a fallback."""
    monkeypatch.setattr(
        sys,
        "argv",
        ["guide", "--config", str(tmp_path / "missing.toml"), "hello"],
    )
    with pytest.raises(FileNotFoundError):
        help_cli.main()


def test_help_sends_argument_message_to_daemon_socket(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI help sends argument messages to the configured daemon socket."""
    _set_os_username(monkeypatch, "alice")
    socket_calls: list[tuple[Path, str, str | None]] = []

    def send_help_request(socket_path: Path, message: str, terminal: str | None) -> str:
        socket_calls.append((socket_path, message, terminal))
        return "daemon response"

    monkeypatch.setattr(help_cli, "_send_help_request", send_help_request)

    assert (
        _run_command(
            monkeypatch,
            ["--config", str(_write_configuration(tmp_path, migrated_database_path)), "hello"],
            daemon_response=None,
        )
        == "daemon response\n"
    )
    assert socket_calls == [(tmp_path / "maker-guide.sock", "hello", None)]


def test_help_preserves_answer_punctuation(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Quoted shell payloads reach the daemon unchanged after Bash removes the quotes."""
    _set_os_username(monkeypatch, "alice")
    socket_messages: list[str] = []

    def send_help_request(_socket_path: Path, message: str, _terminal: str | None) -> str:
        socket_messages.append(message)
        return "answer recorded"

    monkeypatch.setattr(help_cli, "_send_help_request", send_help_request)
    answer_payload = "cut writes stdout (1); wc reads stdin (0)"

    assert (
        _run_command(
            monkeypatch,
            [
                "--config",
                str(_write_configuration(tmp_path, migrated_database_path)),
                "answer",
                answer_payload,
            ],
            daemon_response=None,
        )
        == "answer recorded\n"
    )
    assert socket_messages == [f"answer {answer_payload}"]


def test_help_reports_daemon_connection_failure(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI help prints a useful message when the daemon socket is unavailable."""
    _set_os_username(monkeypatch, "alice")

    assert (
        _run_command(
            monkeypatch,
            ["--config", str(_write_configuration(tmp_path, migrated_database_path)), "hello"],
            daemon_response=None,
        )
        == "I can't reach my remote brain right now. Try me again in a moment.\n"
    )


def test_help_reports_daemon_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A slow daemon response becomes one user-facing line, not a traceback."""

    class _Socket:
        def __enter__(self) -> Self:
            return self

        def __exit__(
            self,
            exception_type: type[BaseException] | None,
            exception: BaseException | None,
            traceback: object,
        ) -> None:
            del exception_type, exception, traceback

        def settimeout(self, timeout_seconds: float) -> None:
            del timeout_seconds

        def connect(self, socket_path: str) -> None:
            del socket_path

        def sendall(self, payload: bytes) -> None:
            del payload

        def recv(self, size: int) -> bytes:
            del size
            raise TimeoutError

    def socket_factory(address_family: int, socket_type: int) -> _Socket:
        del address_family, socket_type
        return _Socket()

    monkeypatch.setattr(help_cli.socket, "socket", socket_factory)

    assert (
        _run_command(
            monkeypatch,
            ["--config", str(_write_configuration(tmp_path, tmp_path / "state.db")), "hello"],
            daemon_response=None,
        )
        == "My remote brain is still thinking. Try me again in a moment.\n"
    )


def test_help_today_is_a_now_alias(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CLI helper preserves today as a compatibility alias for now."""
    _set_os_username(monkeypatch, "alice")
    _write_member(migrated_database_path)
    assert _run_command(
        monkeypatch,
        ["--config", str(_write_configuration(tmp_path, migrated_database_path)), "today"],
        daemon_response="Today's quest: Prove the shell is alive\n\nGoal:",
    ).startswith("Today's quest: Prove the shell is alive\n\nGoal:")


def test_help_ignores_spoofed_environment_identity(
    tmp_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI identity comes from the OS account, not spoofable environment variables."""
    monkeypatch.setenv("USER", "mallory")
    monkeypatch.setenv("USERNAME", "mallory")
    _set_os_username(monkeypatch, "alice")
    socket_calls: list[tuple[Path, str, str | None]] = []

    def send_help_request(socket_path: Path, message: str, terminal: str | None) -> str:
        socket_calls.append((socket_path, message, terminal))
        return FREEFORM_TUTOR_DISABLED_TEXT

    monkeypatch.setattr(help_cli, "_send_help_request", send_help_request)

    assert (
        _run_command(
            monkeypatch,
            ["--config", str(_write_configuration(tmp_path, migrated_database_path)), "hello"],
            daemon_response=None,
        )
        == f"{FREEFORM_TUTOR_DISABLED_TEXT}\n"
    )
    assert socket_calls == [(tmp_path / "maker-guide.sock", "hello", None)]


def _set_os_username(monkeypatch: pytest.MonkeyPatch, username: str) -> None:
    def user_entry_for_id(_user_id: int) -> SimpleNamespace:
        return SimpleNamespace(pw_name=username)

    monkeypatch.setattr(help_cli.os, "getuid", lambda: 1000)
    monkeypatch.setattr(help_cli.pwd, "getpwuid", user_entry_for_id)


def _write_learner(database_path: Path) -> None:
    with connect_database(database_path) as database_connection:
        _write_learner_row(database_connection)


def _write_member(database_path: Path) -> None:
    with connect_database(database_path) as database_connection:
        _write_learner_row(database_connection)
        upsert_membership(
            database_connection,
            CohortMembership(
                handle="alice",
                course_id=CATALOG.course.id,
                joined_at="2026-07-18T09:00:00Z",
            ),
        )
        upsert_course_release(
            database_connection,
            CourseRelease(
                course_id=CATALOG.course.id,
                session_reached="S1",
                released_at="2026-07-18T09:00:00Z",
            ),
        )


def _write_learner_row(database_connection: sqlite3.Connection) -> None:
    upsert_learner(
        database_connection,
        Learner(
            handle="alice",
            joined_at="2026-07-18T09:00:00Z",
            tagline=None,
            created_at="2026-07-18T09:00:00Z",
        ),
    )
