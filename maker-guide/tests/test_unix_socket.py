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
from typing import cast

import pytest

import maker_guide.unix_socket as socket_module
from maker_guide.config import SocketConfig
from maker_guide.events import ShellEvent
from maker_guide.site_check import (
    SITE_CHECK_CASES,
    SiteCheckError,
    SiteCheckReport,
    site_check_report_payload,
)
from maker_guide.unix_socket import HelpChunkWriter, SocketHelpRequest, UnixSocketServer

_SITE_CHECK_REPORT = SiteCheckReport(
    source_sha256="a" * 64,
    cases=tuple((case, True) for case in SITE_CHECK_CASES),
    error=None,
)


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


@pytest.mark.parametrize(
    "result",
    [
        b'{"kind":"site_check_result","report":{}}\n',
        b'{"kind":"help","report":{}}\n',
        b'{"kind":"site_check_result","report":{},"code":"private source"}\n',
        b'{"kind":"site_check_result","kind":"site_check_result","report":{}}\n',
        b'{"kind":"site_check_result","report":{"error":"private source"}}\n',
        b'{"kind":"site_check_result","report":{"error":null,"error":null}}\n',
        json.dumps(
            {
                "kind": "site_check_result",
                "report": site_check_report_payload(_SITE_CHECK_REPORT)
                | {"source_sha256": "b" * 64},
            },
        ).encode()
        + b"\n",
        b"[]\n",
        b"\xff\n",
        b'{"report":"' + b"private source" * 400 + b'"}\n',
        b'{"kind":"site_check_result","report":{}}',
        b"",
    ],
)
async def test_site_check_rejects_bad_results(
    temporary_path: Path,
    result: bytes,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Only a bounded, complete, fixed report is accepted on the pending reader."""

    async def handle_help_request(
        request: SocketHelpRequest,
        chunk_writer: HelpChunkWriter | None,
    ) -> str:
        assert chunk_writer is None
        assert request.site_check_runner is not None
        await request.site_check_runner("a" * 64)
        pytest.fail("malformed report reached grading")

    socket_path = temporary_path / "site-check.sock"
    unix_socket_server = UnixSocketServer(
        SocketConfig(path=socket_path, allowed_user_ids=frozenset({os.getuid()})),
        asyncio.Queue(),
        help_handler=handle_help_request,
    )
    await unix_socket_server.start()
    try:
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(b'{"version":1,"kind":"help","text":"check","supports_site_check":true}\n')
        await writer.drain()
        assert cast("object", json.loads(await reader.readline())) == {
            "ok": True,
            "site_check": {"version": 1, "source_sha256": "a" * 64},
        }
        writer.write(result)
        await writer.drain()
        writer.write_eof()
        response = await asyncio.wait_for(reader.readline(), timeout=1)
        writer.close()
        await writer.wait_closed()
    finally:
        await unix_socket_server.close()
    assert cast("object", json.loads(response)) == {
        "ok": False,
        "execute": True,
        "error": "site check failed",
    }
    assert "private source" not in caplog.text


@pytest.mark.parametrize(
    "payload",
    [
        b'{"kind":"site_check_result","report":{}}\n',
        b'{"version":1,"kind":"help","text":"check","report":{}}\n',
        b'{"version":1,"kind":"help","text":"check","site_check_runner":true}\n',
        b'{"version":1,"kind":"help","text":"check","supports_site_check":1}\n',
        b'{"version":1,"kind":"help","text":"check","stream":"true"}\n',
        b'{"version":true,"kind":"help","text":"check"}\n',
        b'{"version":1,"kind":"help","text":"now","text":"check"}\n',
    ],
)
async def test_site_check_rejects_unsolicited_initial_fields(
    temporary_path: Path,
    payload: bytes,
) -> None:
    """A client cannot submit its own callback or a result before an action."""

    async def handle_help_request(
        request: SocketHelpRequest,
        chunk_writer: HelpChunkWriter | None,
    ) -> str:
        del request, chunk_writer
        pytest.fail("invalid initial request reached help handler")

    socket_path = temporary_path / "site-check.sock"
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    unix_socket_server = UnixSocketServer(
        SocketConfig(path=socket_path, allowed_user_ids=frozenset({os.getuid()})),
        ingest_queue,
        help_handler=handle_help_request,
    )
    await unix_socket_server.start()
    try:
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(payload)
        await writer.drain()
        response = cast("dict[str, object]", json.loads(await reader.readline()))
        writer.close()
        await writer.wait_closed()
    finally:
        await unix_socket_server.close()
    assert response["ok"] is False
    assert ingest_queue.empty()


async def test_site_check_timeout_does_not_allow_a_retry(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stalled local check expires without granting another action."""
    monkeypatch.setattr(socket_module, "SITE_CHECK_TIMEOUT_SECONDS", -1.8)

    async def handle_help_request(
        request: SocketHelpRequest,
        chunk_writer: HelpChunkWriter | None,
    ) -> str:
        del chunk_writer
        assert request.site_check_runner is not None
        with pytest.raises(SiteCheckError):
            await request.site_check_runner("a" * 64)
        with pytest.raises(SiteCheckError):
            await request.site_check_runner("a" * 64)
        return "check unavailable"

    socket_path = temporary_path / "site-check.sock"
    unix_socket_server = UnixSocketServer(
        SocketConfig(path=socket_path, allowed_user_ids=frozenset({os.getuid()})),
        asyncio.Queue(),
        help_handler=handle_help_request,
    )
    await unix_socket_server.start()
    try:
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(b'{"version":1,"kind":"help","text":"now","supports_site_check":true}\n')
        await writer.drain()
        assert b"site_check" in await reader.readline()
        response = await asyncio.wait_for(reader.readline(), timeout=1)
        writer.close()
        await writer.wait_closed()
    finally:
        await unix_socket_server.close()
    assert cast("object", json.loads(response)) == {
        "ok": True,
        "execute": True,
        "text": "check unavailable",
    }


async def test_site_check_stays_on_original_connection_and_preserves_help(
    temporary_path: Path,
) -> None:
    """Another authorized connection cannot answer an action or stall ordinary traffic."""
    completed = asyncio.Event()
    retained_requests: list[SocketHelpRequest] = []

    async def handle_help_request(
        request: SocketHelpRequest,
        chunk_writer: HelpChunkWriter | None,
    ) -> str:
        if request.text == "help":
            assert request.site_check_runner is None
            return "ordinary help"
        assert request.username == pwd.getpwuid(os.getuid()).pw_name
        assert request.site_check_runner is not None
        assert chunk_writer is not None
        retained_requests.append(request)
        chunk_writer("before check")
        assert await request.site_check_runner("a" * 64) == _SITE_CHECK_REPORT
        with pytest.raises(SiteCheckError):
            await request.site_check_runner("a" * 64)
        completed.set()
        chunk_writer("after check")
        return "graded response"

    socket_path = temporary_path / "site-check.sock"
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    unix_socket_server = UnixSocketServer(
        SocketConfig(path=socket_path, allowed_user_ids=frozenset({os.getuid()})),
        ingest_queue,
        help_handler=handle_help_request,
    )
    result = (
        json.dumps(
            {"kind": "site_check_result", "report": site_check_report_payload(_SITE_CHECK_REPORT)},
        ).encode()
        + b"\n"
    )
    await unix_socket_server.start()
    try:
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(
            json.dumps(
                {
                    "version": 1,
                    "kind": "help",
                    "text": "check",
                    "stream": True,
                    "supports_site_check": True,
                }
            ).encode()
            + b"\n",
        )
        await writer.drain()
        assert cast("object", json.loads(await reader.readline())) == {
            "ok": True,
            "chunk": "before check",
        }
        assert cast("object", json.loads(await reader.readline())) == {
            "ok": True,
            "site_check": {"version": 1, "source_sha256": "a" * 64},
        }
        for payload, expected in (
            (result, {"ok": False, "execute": True, "error": "unsupported request kind"}),
            (
                b'{"version":1,"kind":"help","text":"help"}\n',
                {"ok": True, "execute": True, "text": "ordinary help"},
            ),
            (
                b'{"version":1,"type":"preexec","cwd":"/repo","command":"ls"}\n',
                {"ok": True, "execute": True},
            ),
        ):
            other_reader, other_writer = await asyncio.open_unix_connection(str(socket_path))
            other_writer.write(payload)
            await other_writer.drain()
            assert cast("object", json.loads(await other_reader.readline())) == expected
            other_writer.close()
            await other_writer.wait_closed()
        assert not completed.is_set()
        assert ingest_queue.get_nowait().command == "ls"
        ingest_queue.task_done()
        writer.write(result)
        await writer.drain()
        assert cast("object", json.loads(await reader.readline())) == {
            "ok": True,
            "chunk": "after check",
        }
        assert cast("object", json.loads(await reader.readline())) == {
            "ok": True,
            "execute": True,
            "text": "graded response",
        }
        writer.close()
        await writer.wait_closed()
    finally:
        await unix_socket_server.close()
    assert completed.is_set()
    assert retained_requests[0].site_check_runner is not None
    with pytest.raises(SiteCheckError):
        await retained_requests[0].site_check_runner("a" * 64)
