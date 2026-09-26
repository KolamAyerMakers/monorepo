"""Service-lab HELP transport never executes unsolicited or repeated local actions."""

from __future__ import annotations

import asyncio
import json
import os
import pwd
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from typing import Literal, cast

import pytest

import maker_guide.cli.bot as bot_cli
import maker_guide.cli.help as help_cli
from maker_guide.config import AppConfig, DatabaseConfig, IrcConfig, SaslConfig, SocketConfig
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.events import IrcOutboundMessage
from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.service_lab_attempt import get_attempt
from maker_guide.service_lab import (
    SERVICE_LAB_MAX_FRAME_BYTES,
    ServiceLabAction,
    ServiceLabError,
    ServiceLabReport,
    service_lab_action_payload,
    service_lab_report_payload,
)
from maker_guide.site_check import (
    SITE_CHECK_CASES,
    SITE_CHECK_VERSION,
    SiteCheckError,
    SiteCheckReport,
)
from maker_guide.unix_socket import HelpChunkWriter, SocketHelpRequest, UnixSocketServer
from tests.chat import test_service_lab as chat_lab_tests

_ACTION = ServiceLabAction(run_id="a" * 32, scenario="empty-root", operation="start")
_REPORT = ServiceLabReport(
    run_id=_ACTION.run_id,
    scenario=_ACTION.scenario,
    started=True,
    healthy=False,
    unit="private unit changes",
    journal="private diagnostics",
    http_status=404,
)
_ACTION_FRAME = (
    json.dumps({"ok": True, "service_lab": service_lab_action_payload(_ACTION)}).encode() + b"\n"
)
_SITE_CHECK_FRAME = (
    json.dumps(
        {"ok": True, "site_check": {"version": SITE_CHECK_VERSION, "source_sha256": "a" * 64}}
    ).encode()
    + b"\n"
)


class _Socket:
    def __init__(self, response: bytes) -> None:
        self.response = response
        self.sent: list[bytes] = []

    def recv(self, size: int) -> bytes:
        response, self.response = self.response[:size], self.response[size:]
        return response

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        ("start", "now"),
        ("inspect", "check"),
    ],
)
async def test_service_lab_capable_help_roundtrip(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    operation: Literal["start", "inspect"],
    message: str,
) -> None:
    """One kernel-bound continuation returns a full reply without revealing local evidence."""
    action = replace(_ACTION, operation=operation)
    runs: list[ServiceLabAction] = []
    chunks: list[str] = []
    requests: list[SocketHelpRequest] = []

    def run_service_lab(selected: ServiceLabAction) -> ServiceLabReport:
        runs.append(selected)
        return _REPORT

    async def handle_help(request: SocketHelpRequest, writer: HelpChunkWriter | None) -> str:
        requests.append(request)
        assert request.username == pwd.getpwuid(os.getuid()).pw_name
        assert request.supports_service_lab is True
        assert request.service_lab_runner is not None
        assert request.site_check_runner is not None
        assert writer is not None
        assert await request.service_lab_runner(action) == _REPORT
        with pytest.raises(ServiceLabError):
            await request.service_lab_runner(action)
        with pytest.raises(SiteCheckError):
            await request.site_check_runner("a" * 64)
        writer("private diagnostics must not stream")
        return "Read your service logs."

    monkeypatch.setattr(help_cli, "run_service_lab", run_service_lab)
    socket_path = temporary_path / "service-lab.sock"
    server = UnixSocketServer(
        SocketConfig(path=socket_path, allowed_user_ids=frozenset({os.getuid()})),
        asyncio.Queue(),
        help_handler=handle_help,
    )
    await server.start()
    try:
        response = await asyncio.to_thread(
            help_cli._send_help_request,  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            socket_path,
            message,
            None,
            chunks.append,
        )
    finally:
        await server.close()
    assert response == "Read your service logs."
    assert runs == [action]
    assert chunks == []
    assert capsys.readouterr() == ("", "")
    assert requests[0].service_lab_runner is not None
    with pytest.raises(ServiceLabError):
        await requests[0].service_lab_runner(action)


async def test_service_lab_cli_bot_bridge_acknowledges_committed_run(
    migrated_database_path: Path,
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The actual CLI, socket, worker bridge and chat handler share one durable attempt."""
    with closing(connect_database(migrated_database_path)) as database_connection:
        chat_lab_tests._seed_s8_prerequisites(database_connection)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

    def lookup_account(user_id: int) -> pwd.struct_passwd:
        return pwd.struct_passwd(
            ("alice", "x", user_id, os.getgid(), "", str(temporary_path), "/bin/bash")
        )

    monkeypatch.setattr(pwd, "getpwuid", lookup_account)
    actions: list[ServiceLabAction] = []

    def run_service_lab(action: ServiceLabAction) -> ServiceLabReport:
        with closing(connect_database(migrated_database_path)) as observer:
            attempt = get_attempt(
                observer, "alice", CATALOG.course.id, "S8", "break-and-read-error"
            )
            assert attempt is not None
            assert (attempt.run_id, attempt.scenario) == (action.run_id, action.scenario)
            assert (attempt.started_at is None) is (action.operation == "start")
        actions.append(action)
        return replace(_REPORT, run_id=action.run_id, scenario=action.scenario)

    monkeypatch.setattr(help_cli, "run_service_lab", run_service_lab)
    configuration = AppConfig(
        socket=SocketConfig(
            path=temporary_path / "bridge.sock", allowed_user_ids=frozenset({os.getuid()})
        ),
        database=DatabaseConfig(path=migrated_database_path),
        irc=IrcConfig(
            server="irc.example",
            port=6697,
            nickname="guide",
            username="guide",
            realname="Guide",
            channels=("#lf2607",),
            sasl=SaslConfig(username="guide", password="secret"),
        ),
    )
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()

    async def handle_help(request: SocketHelpRequest, writer: HelpChunkWriter | None) -> str:
        return await bot_cli._handle_socket_help_request(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            request,
            configuration,
            None,
            writer,
            outbound_queue,
        )

    server = UnixSocketServer(configuration.socket, asyncio.Queue(), help_handler=handle_help)
    await server.start()
    try:
        for message in ("now", "check"):
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    help_cli._send_help_request,  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
                    configuration.socket.path,
                    message,
                    None,
                ),
                timeout=3,
            )
            assert "private diagnostics" not in response
    finally:
        await server.close()
    assert [action.operation for action in actions] == ["start", "inspect"]
    with closing(connect_database(migrated_database_path)) as database_connection:
        attempt = get_attempt(
            database_connection, "alice", CATALOG.course.id, "S8", "break-and-read-error"
        )
        assert attempt is not None
        assert attempt.started_at is not None
        assert {action.run_id for action in actions} == {attempt.run_id}


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        ("start", "today"),
        ("inspect", "now"),
        ("inspect", "answer I read the logs"),
        ("inspect", "why is my service failing?"),
    ],
)
def test_service_lab_cli_accepts_other_authorized_intents(
    monkeypatch: pytest.MonkeyPatch,
    operation: Literal["start", "inspect"],
    message: str,
) -> None:
    """Accepted aliases and inspection intents need no additional socket lifecycle."""
    actions: list[ServiceLabAction] = []

    def run_service_lab(action: ServiceLabAction) -> ServiceLabReport:
        actions.append(action)
        return _REPORT

    monkeypatch.setattr(help_cli, "run_service_lab", run_service_lab)
    client = _Socket(
        _ACTION_FRAME.replace(b'"start"', json.dumps(operation).encode())
        + b'{"ok":true,"text":"final hint"}\n'
    )
    assert help_cli._read_help_response(client, None, message) == "final hint"  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    assert actions == [replace(_ACTION, operation=operation)]
    assert len(client.sent) == 1


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        ("start", "help"),
        ("start", "progress"),
        ("start", "check"),
        ("start", "answer now"),
        ("start", "please start a fault now"),
        ("inspect", "help"),
        ("inspect", "progress"),
        ("inspect", "thank alice for helping"),
    ],
)
def test_service_lab_cli_rejects_action_without_original_intent(
    monkeypatch: pytest.MonkeyPatch,
    operation: Literal["start", "inspect"],
    message: str,
) -> None:
    """Server-selected mutations still require the learner's original now intent."""

    def unexpected_run(action: ServiceLabAction) -> ServiceLabReport:
        del action
        pytest.fail("unrequested local execution")

    monkeypatch.setattr(help_cli, "run_service_lab", unexpected_run)
    client = _Socket(_ACTION_FRAME.replace(b'"start"', json.dumps(operation).encode()))
    assert (
        help_cli._read_help_response(client, None, message)  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        == help_cli._BAD_HELP_RESPONSE_TEXT  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    )
    assert client.sent == []


@pytest.mark.parametrize(
    "frame",
    [
        _ACTION_FRAME.replace(b'"version": 1', b'"version": true'),
        _ACTION_FRAME.replace(b'"version": 1', b'"version": 2'),
        _ACTION_FRAME.replace(b'"version": 1', b'"version": 1, "version": 1'),
        _ACTION_FRAME.replace(b'"start"', b'"restart"'),
        _ACTION_FRAME.replace(b'"empty-root"', b'"arbitrary-command"'),
        _ACTION_FRAME.replace(b"a" * 32, b"../unit"),
        _ACTION_FRAME.replace(b'"operation":', b'"path": "private path", "operation":'),
        _ACTION_FRAME.replace(b'"ok": true', b'"ok": false'),
        _ACTION_FRAME.replace(b'"ok": true', b'"ok": true, "site_check": {}'),
        _ACTION_FRAME[:-1],
        b'{"ok":true,"service_lab":null}\n',
        b'{"ok":true,"service_lab":' + b" " * SERVICE_LAB_MAX_FRAME_BYTES + b"{}}\n",
    ],
)
def test_service_lab_cli_rejects_malformed_action_before_execution(
    monkeypatch: pytest.MonkeyPatch,
    frame: bytes,
) -> None:
    """Malformed action envelopes cannot reach the learner runner."""

    def unexpected_run(action: ServiceLabAction) -> ServiceLabReport:
        del action
        pytest.fail("malformed local execution")

    monkeypatch.setattr(help_cli, "run_service_lab", unexpected_run)
    client = _Socket(frame)
    assert (
        help_cli._read_help_response(client, None, "now")  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        == help_cli._BAD_HELP_RESPONSE_TEXT  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    )
    assert client.sent == []


@pytest.mark.parametrize(
    "frames",
    [
        _ACTION_FRAME * 2,
        _ACTION_FRAME + _SITE_CHECK_FRAME,
        _SITE_CHECK_FRAME + _ACTION_FRAME,
    ],
)
def test_service_lab_cli_shares_one_action_budget(
    monkeypatch: pytest.MonkeyPatch,
    frames: bytes,
) -> None:
    """Neither repeated actions nor switching action families permits a second execution."""
    runs: list[str] = []

    def run_service_lab(action: ServiceLabAction) -> ServiceLabReport:
        runs.append(action.run_id)
        return _REPORT

    def run_site_check(source_sha256: str) -> SiteCheckReport:
        runs.append(source_sha256)
        return SiteCheckReport(
            source_sha256=source_sha256,
            cases=tuple((case, True) for case in SITE_CHECK_CASES),
            error=None,
        )

    monkeypatch.setattr(help_cli, "run_service_lab", run_service_lab)
    monkeypatch.setattr(help_cli, "run_site_check", run_site_check)
    client = _Socket(frames)
    assert (
        help_cli._read_help_response(client, None, "now")  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        == help_cli._BAD_HELP_RESPONSE_TEXT  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    )
    assert len(runs) == len(client.sent) == 1


def test_service_lab_cli_sends_evidence_only_to_daemon(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Even an incoming chunk after the action cannot expose raw service diagnostics."""

    def run_service_lab(action: ServiceLabAction) -> ServiceLabReport:
        assert action == _ACTION
        return _REPORT

    monkeypatch.setattr(help_cli, "run_service_lab", run_service_lab)
    chunks: list[str] = []
    client = _Socket(
        _ACTION_FRAME
        + b'{"ok":true,"chunk":""}\n'
        + b'{"ok":true,"chunk":"private diagnostics"}\n'
        + b'{"ok":true,"text":"Read your service logs."}\n'
    )
    assert (
        help_cli._read_help_response(client, chunks.append, "now")  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        == "Read your service logs."
    )
    assert cast("object", json.loads(client.sent[0])) == {
        "kind": "service_lab_result",
        "report": service_lab_report_payload(_REPORT),
    }
    assert chunks == []
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("limit_delta", [0, -1])
def test_service_lab_cli_bounds_report_envelope_and_newline(
    monkeypatch: pytest.MonkeyPatch,
    limit_delta: int,
) -> None:
    """A valid report payload must still fit when wrapped in its complete wire frame."""

    def run_service_lab(action: ServiceLabAction) -> ServiceLabReport:
        assert action == _ACTION
        return _REPORT

    reply = (
        json.dumps(
            {"kind": "service_lab_result", "report": service_lab_report_payload(_REPORT)},
            separators=(",", ":"),
        ).encode()
        + b"\n"
    )
    assert len(json.dumps(service_lab_report_payload(_REPORT)).encode()) < len(reply) + limit_delta
    monkeypatch.setattr(help_cli, "run_service_lab", run_service_lab)
    monkeypatch.setattr(help_cli, "SERVICE_LAB_MAX_FRAME_BYTES", len(reply) + limit_delta)
    client = _Socket(_ACTION_FRAME + b'{"ok":true,"text":"final hint"}\n')
    response = help_cli._read_help_response(client, None, "now")  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
    if limit_delta == 0:
        assert response == "final hint"
        assert client.sent == [reply]
    else:
        assert response == help_cli._BAD_HELP_RESPONSE_TEXT  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        assert client.sent == []
