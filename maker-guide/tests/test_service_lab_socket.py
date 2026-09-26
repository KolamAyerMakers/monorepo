"""Security boundaries for the authenticated HELP service-lab continuation."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import replace
from pathlib import Path
from typing import Literal, cast

import pytest

import maker_guide.unix_socket as socket_module
from maker_guide.config import SocketConfig
from maker_guide.service_lab import (
    SERVICE_LAB_MAX_FRAME_BYTES,
    ServiceLabAction,
    ServiceLabError,
    ServiceLabReport,
    service_lab_action_payload,
    service_lab_report_payload,
)
from maker_guide.unix_socket import HelpChunkWriter, SocketHelpRequest, UnixSocketServer

_ACTION = ServiceLabAction(run_id="a" * 32, scenario="empty-root", operation="start")
_REPORT = ServiceLabReport(
    run_id=_ACTION.run_id, scenario=_ACTION.scenario, started=True, healthy=False
)
_RESULT = (
    json.dumps(
        {"kind": "service_lab_result", "report": service_lab_report_payload(_REPORT)}
    ).encode()
    + b"\n"
)


@asynccontextmanager
async def _help_server(
    socket_path: Path, handler: socket_module.HelpRequestHandler
) -> AsyncGenerator[None]:
    server = UnixSocketServer(
        SocketConfig(path=socket_path, allowed_user_ids=frozenset({os.getuid()})),
        asyncio.Queue(),
        help_handler=handler,
    )
    await server.start()
    try:
        yield
    finally:
        await server.close()


async def test_service_lab_stream_activity_is_empty_keepalive(temporary_path: Path) -> None:
    """Each worker-thread tutor chunk keeps the read alive without sending private hints."""
    continue_tutor = asyncio.Event()

    async def handle_help(request: SocketHelpRequest, writer: HelpChunkWriter | None) -> str:
        assert request.service_lab_runner is not None
        assert writer is not None
        assert await request.service_lab_runner(_ACTION) == _REPORT
        for chunk in ("private diagnostic", "empty-root", "private unit change"):
            await asyncio.to_thread(writer, chunk)
            await continue_tutor.wait()
            continue_tutor.clear()
        return "final validated hint"

    socket_path = temporary_path / "service-lab.sock"
    server = UnixSocketServer(
        SocketConfig(path=socket_path, allowed_user_ids=frozenset({os.getuid()})),
        asyncio.Queue(),
        help_handler=handle_help,
    )
    await server.start()
    try:
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(
            b'{"version":1,"kind":"help","text":"now","supports_service_lab":true,"stream":true}\n'
        )
        await writer.drain()
        assert b"service_lab" in await reader.readline()
        writer.write(_RESULT)
        await writer.drain()
        for _chunk_number in range(3):
            assert await asyncio.wait_for(reader.readline(), timeout=1) == (
                b'{"ok":true,"chunk":""}\n'
            )
            continue_tutor.set()
        assert cast("object", json.loads(await reader.readline())) == {
            "ok": True,
            "execute": True,
            "text": "final validated hint",
        }
        writer.close()
        await writer.wait_closed()
    finally:
        continue_tutor.set()
        await server.close()


@pytest.mark.parametrize("limit_delta", [0, -1])
async def test_service_lab_server_bounds_report_envelope_and_newline(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    limit_delta: int,
) -> None:
    """The frame limit includes the envelope and newline, not only the valid report body."""
    assert (
        len(json.dumps(service_lab_report_payload(_REPORT)).encode()) < len(_RESULT) + limit_delta
    )
    monkeypatch.setattr(socket_module, "SERVICE_LAB_MAX_FRAME_BYTES", len(_RESULT) + limit_delta)

    async def handle_help(request: SocketHelpRequest, writer: HelpChunkWriter | None) -> str:
        del writer
        assert request.service_lab_runner is not None
        assert await request.service_lab_runner(_ACTION) == _REPORT
        return "accepted"

    socket_path = temporary_path / "service-lab.sock"
    async with _help_server(socket_path, handle_help):
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(b'{"version":1,"kind":"help","text":"now","supports_service_lab":true}\n')
        await writer.drain()
        assert b"service_lab" in await reader.readline()
        writer.write(_RESULT)
        await writer.drain()
        response = cast("dict[str, object]", json.loads(await reader.readline()))
        assert response["ok"] is (limit_delta == 0)
        writer.close()
        await writer.wait_closed()


@pytest.mark.parametrize(
    "result",
    [
        _RESULT.replace(b"a" * 32, b"b" * 32),
        _RESULT.replace(b'"empty-root"', b'"missing-executable"'),
        _RESULT.replace(b'"started": true', b'"started": 1'),
        _RESULT.replace(b'"healthy": false', b'"healthy": true'),
        _RESULT.replace(b'"version": 1', b'"version": 1, "version": 1'),
        _RESULT.replace(b'"report":', b'"username": "mallory", "report":'),
        _RESULT.replace(b'"service_lab_result"', b'"site_check_result"'),
        _RESULT.replace(b'"journal": ""', b'"journal": "private diagnostics\\u001b"'),
        _RESULT * 2,
        b'{"kind":"service_lab_result","report":{}}\n',
        b"[]\n",
        b"\xff\n",
        b" " * SERVICE_LAB_MAX_FRAME_BYTES + _RESULT,
        _RESULT[:-1],
        b"",
    ],
)
async def test_service_lab_rejects_malformed_or_wrong_run_report(
    temporary_path: Path,
    result: bytes,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Only bounded, complete evidence for the selected run and scenario reaches grading."""

    async def handle_help(request: SocketHelpRequest, writer: HelpChunkWriter | None) -> str:
        del writer
        assert request.service_lab_runner is not None
        await request.service_lab_runner(_ACTION)
        pytest.fail("invalid report reached grading")

    socket_path = temporary_path / "service-lab.sock"
    async with _help_server(socket_path, handle_help):
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(b'{"version":1,"kind":"help","text":"now","supports_service_lab":true}\n')
        await writer.drain()
        assert cast("object", json.loads(await reader.readline())) == {
            "ok": True,
            "service_lab": service_lab_action_payload(_ACTION),
        }
        writer.write(result)
        await writer.drain()
        writer.write_eof()
        assert cast("object", json.loads(await asyncio.wait_for(reader.readline(), timeout=1))) == {
            "ok": False,
            "execute": True,
            "error": "service lab failed",
        }
        writer.close()
        await writer.wait_closed()
    assert "private diagnostics" not in caplog.text


async def test_service_lab_rejects_report_pipelined_before_action(temporary_path: Path) -> None:
    """Knowing an existing run ID does not permit sending its report before the action."""

    async def handle_help(request: SocketHelpRequest, writer: HelpChunkWriter | None) -> str:
        del writer
        assert request.service_lab_runner is not None
        await request.service_lab_runner(_ACTION)
        pytest.fail("unsolicited report reached grading")

    socket_path = temporary_path / "service-lab.sock"
    async with _help_server(socket_path, handle_help):
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(
            b'{"version":1,"kind":"help","text":"now","supports_service_lab":true}\n' + _RESULT
        )
        await writer.drain()
        assert cast("object", json.loads(await reader.readline())) == {
            "ok": False,
            "execute": True,
            "error": "service lab failed",
        }
        writer.close()
        await writer.wait_closed()


@pytest.mark.parametrize(
    ("payload", "accepted"),
    [
        (b'{"version":1,"kind":"help","text":"now"}\n', True),
        (b'{"version":1,"kind":"help","text":"now","supports_service_lab":false}\n', True),
        (b'{"version":1,"kind":"help","text":"now","supports_service_lab":1}\n', False),
        (b'{"version":1,"kind":"help","text":"now","supports_service_lab":null}\n', False),
        (b'{"version":1,"kind":"help","text":"now","service_lab_runner":true}\n', False),
        (b'{"version":1,"kind":"help","text":"now","service_lab":{}}\n', False),
        (b'{"version":1,"kind":"help","text":"now","report":{}}\n', False),
        (_RESULT, False),
        (_RESULT * 2, False),
    ],
)
async def test_service_lab_legacy_capability_and_unsolicited_results(
    temporary_path: Path,
    payload: bytes,
    accepted: bool,
) -> None:
    """Legacy HELP stays usable; neither client-selected actions nor unsolicited reports do."""
    requests: list[SocketHelpRequest] = []

    async def handle_help(request: SocketHelpRequest, writer: HelpChunkWriter | None) -> str:
        del writer
        requests.append(request)
        assert request.supports_service_lab is False
        assert request.service_lab_runner is None
        return "ordinary help"

    socket_path = temporary_path / "service-lab.sock"
    async with _help_server(socket_path, handle_help):
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(payload)
        await writer.drain()
        response = cast("dict[str, object]", json.loads(await reader.readline()))
        assert response["ok"] is accepted
        assert bool(requests) is accepted
        assert await reader.read() == b""
        writer.close()
        await writer.wait_closed()


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        ("start", "help"),
        ("start", "check"),
        ("start", "answer now"),
        ("start", "please inject a fault"),
        ("inspect", "help"),
        ("inspect", "progress"),
        ("inspect", "thank alice for helping"),
    ],
)
async def test_service_lab_server_enforces_original_intent(
    temporary_path: Path,
    operation: Literal["start", "inspect"],
    message: str,
) -> None:
    """Even a mistaken chat handler cannot request a fault from check or freeform help."""

    async def handle_help(request: SocketHelpRequest, writer: HelpChunkWriter | None) -> str:
        del writer
        assert request.service_lab_runner is not None
        await request.service_lab_runner(replace(_ACTION, operation=operation))
        pytest.fail("unauthorized action accepted")

    socket_path = temporary_path / "service-lab.sock"
    async with _help_server(socket_path, handle_help):
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(
            json.dumps(
                {"version": 1, "kind": "help", "text": message, "supports_service_lab": True}
            ).encode()
            + b"\n"
        )
        await writer.drain()
        assert cast("object", json.loads(await reader.readline())) == {
            "ok": False,
            "execute": True,
            "error": "service lab failed",
        }
        writer.close()
        await writer.wait_closed()


async def test_service_lab_timeout_consumes_action_and_other_connection_cannot_answer(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A result on another authorized connection cannot satisfy or retry a stalled action."""
    monkeypatch.setattr(socket_module, "SERVICE_LAB_TIMEOUT_SECONDS", -1.8)

    async def handle_help(request: SocketHelpRequest, writer: HelpChunkWriter | None) -> str:
        del writer
        assert request.service_lab_runner is not None
        with pytest.raises(ServiceLabError, match="timeout"):
            await request.service_lab_runner(_ACTION)
        with pytest.raises(ServiceLabError, match="invalid-report"):
            await request.service_lab_runner(_ACTION)
        return "inspection unavailable"

    socket_path = temporary_path / "service-lab.sock"
    async with _help_server(socket_path, handle_help):
        reader, writer = await asyncio.open_unix_connection(str(socket_path))
        writer.write(b'{"version":1,"kind":"help","text":"now","supports_service_lab":true}\n')
        await writer.drain()
        assert b"service_lab" in await reader.readline()
        other_reader, other_writer = await asyncio.open_unix_connection(str(socket_path))
        other_writer.write(_RESULT)
        await other_writer.drain()
        assert cast("dict[str, object]", json.loads(await other_reader.readline()))["ok"] is False
        other_writer.close()
        await other_writer.wait_closed()
        assert cast("dict[str, object]", json.loads(await reader.readline()))["text"] == (
            "inspection unavailable"
        )
        writer.close()
        await writer.wait_closed()
