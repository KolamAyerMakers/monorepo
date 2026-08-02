"""Tests for Unix socket ingestion."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import pwd
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    import pytest

from maker_guide.config import SocketConfig
from maker_guide.events import ShellEvent
from maker_guide.unix_socket import HelpChunkWriter, SocketHelpRequest, UnixSocketServer


def _expected_shell_event() -> ShellEvent:
    return ShellEvent(
        user_id=os.getuid(),
        username=pwd.getpwuid(os.getuid()).pw_name,
        process_id=os.getpid(),
        phase="before",
        cwd="/repo",
        command="git status",
        shell="bash",
        tty=None,
        exit_status=None,
        execute=True,
        timestamp=datetime.now(UTC),
    )


async def test_unix_socket_accepts_authorized_peer(temporary_path: Path) -> None:
    """Authorized local peers can submit one JSON Lines event."""
    socket_path = temporary_path / "preexec.sock"
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue(maxsize=1)
    unix_socket_server = UnixSocketServer(
        SocketConfig(path=socket_path, allowed_user_ids=frozenset({os.getuid()})),
        ingest_queue,
    )
    await unix_socket_server.start()

    try:
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(
            b'{"version":1,"type":"preexec","cwd":"/repo","command":"git status"}\n',
        )
        await writer.drain()
        response = await reader.readline()
        writer.close()
        await writer.wait_closed()
    finally:
        await unix_socket_server.close()

    loaded = cast("object", json.loads(response.decode("utf-8")))
    assert loaded == {"ok": True, "execute": True}
    event = ingest_queue.get_nowait()
    fixed_timestamp = datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC)
    assert replace(event, timestamp=fixed_timestamp) == replace(
        _expected_shell_event(),
        timestamp=fixed_timestamp,
    )


async def test_unix_socket_rejects_queue_overflow(temporary_path: Path) -> None:
    """The socket handler fails fast instead of blocking shell producers."""
    socket_path = temporary_path / "preexec.sock"
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue(maxsize=1)
    ingest_queue.put_nowait(
        ShellEvent(
            user_id=os.getuid(),
            username="already-full",
            process_id=os.getpid(),
            phase="before",
            cwd="/repo",
            command="true",
            shell="bash",
            tty=None,
            exit_status=None,
            execute=True,
            timestamp=datetime.now(UTC),
        ),
    )
    unix_socket_server = UnixSocketServer(
        SocketConfig(path=socket_path, allowed_user_ids=frozenset({os.getuid()})),
        ingest_queue,
    )
    await unix_socket_server.start()

    try:
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(
            b'{"version":1,"type":"preexec","cwd":"/repo","command":"git status"}\n',
        )
        await writer.drain()
        response = await reader.readline()
        writer.close()
        await writer.wait_closed()
    finally:
        await unix_socket_server.close()

    loaded = cast("object", json.loads(response.decode("utf-8")))
    assert loaded == {"ok": False, "execute": True, "error": "queue full"}


async def test_unix_socket_logs_silent_queue_overflow(
    temporary_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """One-way hook traffic stays silent to the client but warns operators on drops."""
    socket_path = temporary_path / "preexec.sock"
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue(maxsize=1)
    ingest_queue.put_nowait(_expected_shell_event())
    unix_socket_server = UnixSocketServer(
        SocketConfig(path=socket_path, allowed_user_ids=frozenset({os.getuid()})),
        ingest_queue,
    )
    await unix_socket_server.start()

    try:
        caplog.set_level(logging.WARNING, logger="maker_guide.unix_socket")
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(
            json.dumps(
                {
                    "version": 1,
                    "type": "preexec",
                    "cwd": "/repo",
                    "command": "git status",
                    "reply": False,
                },
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n",
        )
        await writer.drain()
        response = await asyncio.wait_for(reader.readline(), timeout=1)
        writer.close()
        await writer.wait_closed()
    finally:
        await unix_socket_server.close()

    assert response == b""
    assert "dropped socket event because ingest queue is full" in caplog.text
    assert "command='git status'" in caplog.text


async def test_unix_socket_accepts_one_way_preexec_event(temporary_path: Path) -> None:
    """Preexec telemetry can skip the response write."""
    socket_path = temporary_path / "preexec.sock"
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue(maxsize=1)
    unix_socket_server = UnixSocketServer(
        SocketConfig(path=socket_path, allowed_user_ids=frozenset({os.getuid()})),
        ingest_queue,
    )
    await unix_socket_server.start()

    try:
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(
            json.dumps(
                {
                    "version": 1,
                    "type": "preexec",
                    "cwd": "/repo",
                    "command": "rm -rf /tmp/nope",
                    "reply": False,
                },
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n",
        )
        await writer.drain()
        response = await asyncio.wait_for(reader.readline(), timeout=1)
        writer.close()
        await writer.wait_closed()
    finally:
        await unix_socket_server.close()

    assert response == b""
    event = ingest_queue.get_nowait()
    fixed_timestamp = datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC)
    assert replace(event, timestamp=fixed_timestamp) == replace(
        ShellEvent(
            user_id=os.getuid(),
            username=pwd.getpwuid(os.getuid()).pw_name,
            process_id=os.getpid(),
            phase="before",
            cwd="/repo",
            command="rm -rf /tmp/nope",
            shell="bash",
            tty=None,
            exit_status=None,
            execute=True,
            timestamp=fixed_timestamp,
        ),
        timestamp=fixed_timestamp,
    )


async def test_unix_socket_accepts_one_way_postexec_event(temporary_path: Path) -> None:
    """Postexec telemetry can skip the response write."""
    socket_path = temporary_path / "preexec.sock"
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue(maxsize=1)
    unix_socket_server = UnixSocketServer(
        SocketConfig(path=socket_path, allowed_user_ids=frozenset({os.getuid()})),
        ingest_queue,
    )
    await unix_socket_server.start()

    try:
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(
            json.dumps(
                {
                    "version": 1,
                    "type": "postexec",
                    "cwd": "/repo",
                    "command": "make test",
                    "exit_status": 2,
                    "reply": False,
                },
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n",
        )
        await writer.drain()
        response = await asyncio.wait_for(reader.readline(), timeout=1)
        writer.close()
        await writer.wait_closed()
    finally:
        await unix_socket_server.close()

    assert response == b""
    event = ingest_queue.get_nowait()
    fixed_timestamp = datetime(2026, 5, 26, 12, 0, 0, tzinfo=UTC)
    assert replace(event, timestamp=fixed_timestamp) == replace(
        ShellEvent(
            user_id=os.getuid(),
            username=pwd.getpwuid(os.getuid()).pw_name,
            process_id=os.getpid(),
            phase="after",
            cwd="/repo",
            command="make test",
            shell="bash",
            tty=None,
            exit_status=2,
            execute=True,
            timestamp=fixed_timestamp,
        ),
        timestamp=fixed_timestamp,
    )


async def test_unix_socket_routes_help_request_to_handler(temporary_path: Path) -> None:
    """CLI help requests are answered by the daemon-side handler."""
    socket_path = temporary_path / "preexec.sock"
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue(maxsize=1)
    help_requests: list[SocketHelpRequest] = []

    async def handle_help_request(
        help_request: SocketHelpRequest,
        chunk_writer: HelpChunkWriter | None,
    ) -> str:
        assert chunk_writer is None
        help_requests.append(help_request)
        return "daemon response"

    unix_socket_server = UnixSocketServer(
        SocketConfig(path=socket_path, allowed_user_ids=frozenset({os.getuid()})),
        ingest_queue,
        help_handler=handle_help_request,
    )
    await unix_socket_server.start()

    try:
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(
            json.dumps(
                {
                    "version": 1,
                    "kind": "help",
                    "text": "explain chmod",
                    "terminal": "/dev/pts/1",
                },
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n",
        )
        await writer.drain()
        response = await reader.readline()
        writer.close()
        await writer.wait_closed()
    finally:
        await unix_socket_server.close()

    assert cast("object", json.loads(response.decode("utf-8"))) == {
        "ok": True,
        "execute": True,
        "text": "daemon response",
    }
    assert help_requests == [
        SocketHelpRequest(
            username=pwd.getpwuid(os.getuid()).pw_name,
            terminal="/dev/pts/1",
            text="explain chmod",
        ),
    ]
    assert ingest_queue.empty()


async def test_unix_socket_waits_for_pending_events_before_handling_help(
    temporary_path: Path,
) -> None:
    """Help checks see observations that were accepted before the request."""
    socket_path = temporary_path / "preexec.sock"
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue(maxsize=1)
    handled_request = asyncio.Event()

    async def handle_help_request(
        help_request: SocketHelpRequest,
        chunk_writer: HelpChunkWriter | None,
    ) -> str:
        assert help_request.text == "check"
        assert chunk_writer is None
        handled_request.set()
        return "daemon response"

    unix_socket_server = UnixSocketServer(
        SocketConfig(path=socket_path, allowed_user_ids=frozenset({os.getuid()})),
        ingest_queue,
        help_handler=handle_help_request,
    )
    await unix_socket_server.start()
    await ingest_queue.put(
        ShellEvent(
            user_id=os.getuid(),
            username=pwd.getpwuid(os.getuid()).pw_name,
            process_id=os.getpid(),
            phase="after",
            cwd="/repo",
            command="uptime",
            shell="bash",
            tty=None,
            exit_status=0,
            execute=True,
            timestamp=datetime.now(UTC),
        ),
    )

    try:
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(b'{"version":1,"kind":"help","text":"check","terminal":null}\n')
        await writer.drain()
        await asyncio.sleep(0)
        assert not handled_request.is_set()
        ingest_queue.get_nowait()
        ingest_queue.task_done()
        response = await reader.readline()
        writer.close()
        await writer.wait_closed()
    finally:
        await unix_socket_server.close()

    assert handled_request.is_set()
    assert cast("object", json.loads(response.decode("utf-8"))) == {
        "ok": True,
        "execute": True,
        "text": "daemon response",
    }


async def test_unix_socket_streams_help_chunks(temporary_path: Path) -> None:
    """CLI help requests can receive JSONL chunks before the final response."""
    socket_path = temporary_path / "preexec.sock"
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue(maxsize=1)

    async def handle_help_request(
        help_request: SocketHelpRequest,
        chunk_writer: HelpChunkWriter | None,
    ) -> str:
        assert help_request.stream is True
        assert chunk_writer is not None
        chunk_writer("hello ")
        chunk_writer("there")
        return "hello there"

    unix_socket_server = UnixSocketServer(
        SocketConfig(path=socket_path, allowed_user_ids=frozenset({os.getuid()})),
        ingest_queue,
        help_handler=handle_help_request,
    )
    await unix_socket_server.start()

    try:
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(
            json.dumps(
                {
                    "version": 1,
                    "kind": "help",
                    "text": "explain chmod",
                    "terminal": "/dev/pts/1",
                    "stream": True,
                },
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n",
        )
        await writer.drain()
        responses = [
            cast("dict[str, object]", json.loads((await reader.readline()).decode("utf-8"))),
            cast("dict[str, object]", json.loads((await reader.readline()).decode("utf-8"))),
            cast("dict[str, object]", json.loads((await reader.readline()).decode("utf-8"))),
        ]
        writer.close()
        await writer.wait_closed()
    finally:
        await unix_socket_server.close()

    assert responses == [
        {"ok": True, "chunk": "hello "},
        {"ok": True, "chunk": "there"},
        {"ok": True, "execute": True, "text": "hello there"},
    ]


async def test_unix_socket_rejects_stream_limit_overrun(temporary_path: Path) -> None:
    """Oversized events receive JSON errors instead of handler exceptions."""
    socket_path = temporary_path / "preexec.sock"
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue(maxsize=1)
    unix_socket_server = UnixSocketServer(
        SocketConfig(
            path=socket_path,
            allowed_user_ids=frozenset({os.getuid()}),
            max_line_bytes=10,
        ),
        ingest_queue,
    )
    await unix_socket_server.start()

    try:
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(b'{"version":1,"type":"preexec"}\n')
        await writer.drain()
        response = await reader.readline()
        writer.close()
        await writer.wait_closed()
    finally:
        await unix_socket_server.close()

    loaded = cast("object", json.loads(response.decode("utf-8")))
    assert loaded == {"ok": False, "execute": True, "error": "payload too large"}
