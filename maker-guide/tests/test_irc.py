"""Tests for IRC SASL registration."""

from __future__ import annotations

import asyncio
import base64
import sqlite3
import threading
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import replace
from pathlib import Path
from textwrap import dedent
from typing import cast, override

import pytest

from maker_guide import irc
from maker_guide.chat.contract import (
    CHAT_INPUT_TOO_LONG_TEXT,
    DEFAULT_CHAT_MAX_INPUT_CHARS,
    ChatError,
)
from maker_guide.config import IrcConfig, SaslConfig
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.events import IrcOutboundMessage
from maker_guide.irc import (
    IrcClient,
    IrcClientOptions,
    IrcError,
    IrcPrivateMessage,
    split_irc_text,
)
from maker_guide.llm_tutor import TutorError, TutorRequest, TutorResponse
from maker_guide.repositories.audit_event import list_recent_audit_events_by_type
from maker_guide.repositories.cohort_membership import CohortMembership, upsert_membership
from maker_guide.repositories.course_release import CourseRelease, upsert_course_release
from maker_guide.repositories.help_interaction import list_recent_help_interactions
from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.learner import Learner, upsert_learner
from maker_guide.repositories.quest_assignment import QuestAssignment, assign_quest
from maker_guide.repositories.quest_completion import (
    QuestCompletion,
)
from maker_guide.repositories.quest_completion import (
    complete_quest as complete_quest_repository,
)
from maker_guide.repositories.score_ledger import ScoreLedgerEntry, add_score_entry
from maker_guide.repositories.session_objective_completion import (
    SessionObjectiveCompletion,
    complete_session_objective,
    list_completed_objective_ids,
)

ServerHandler = Callable[[asyncio.StreamReader, asyncio.StreamWriter], Awaitable[None]]

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


class _ChatErrorIrcClient(IrcClient):
    @override
    async def handle_private_message(
        self,
        private_message: IrcPrivateMessage,
        connection_token: object | None = None,
    ) -> None:
        if connection_token is None:
            raise ChatError(f"synthetic chat failure without token for {private_message.sender}")
        raise ChatError(f"synthetic chat failure with token for {private_message.sender}")


class _SqliteErrorIrcClient(IrcClient):
    @override
    async def handle_private_message(
        self,
        private_message: IrcPrivateMessage,
        connection_token: object | None = None,
    ) -> None:
        del private_message, connection_token
        raise sqlite3.OperationalError("database is locked")


class _TutorErrorIrcClient(IrcClient):
    @override
    async def handle_private_message(
        self,
        private_message: IrcPrivateMessage,
        connection_token: object | None = None,
    ) -> None:
        del private_message, connection_token
        raise TutorError("provider unavailable")


class _SenderLoopIrcClient(IrcClient):
    async def run_sender_loop(self, writer: asyncio.StreamWriter) -> None:
        await self._sender_loop(writer)


class _BlockingEvidenceIrcClient(IrcClient):
    def __init__(
        self,
        configuration: IrcConfig,
        outbound_queue: asyncio.Queue[IrcOutboundMessage],
        persistence_started_event: threading.Event,
        release_persistence_event: threading.Event,
        options: IrcClientOptions,
    ) -> None:
        super().__init__(configuration, outbound_queue, options)
        self._persistence_started_event = persistence_started_event
        self._release_persistence_event = release_persistence_event

    @override
    def _persist_evidence(  # pyright: ignore[reportPrivateUsage]
        self,
        evidence: irc._IrcEvidence,  # pyright: ignore[reportPrivateUsage]
    ) -> tuple[str, ...] | None:
        del evidence
        self._persistence_started_event.set()
        if not self._release_persistence_event.wait(timeout=5.0):
            raise RuntimeError("test evidence persistence was not released")
        return ()


class _RecordingWriter:
    def __init__(
        self,
        *,
        fail_on_drain: bool = False,
        write_event: asyncio.Event | None = None,
        blocked_drain_started_event: asyncio.Event | None = None,
    ) -> None:
        self.fail_on_drain = fail_on_drain
        self.write_event = write_event
        self.blocked_drain_started_event = blocked_drain_started_event
        self.lines: list[str] = []

    def write(self, data: bytes) -> None:
        self.lines.append(data.decode("utf-8"))
        if self.write_event is not None:
            self.write_event.set()

    async def drain(self) -> None:
        if self.fail_on_drain:
            raise OSError("synthetic send failure")
        if self.blocked_drain_started_event is not None:
            self.blocked_drain_started_event.set()
            await asyncio.Event().wait()


class _BlockingTutorClient:
    def __init__(self, release_event: threading.Event) -> None:
        self._release_event = release_event
        self._lock = threading.Lock()
        self.requests: list[TutorRequest] = []
        self.request_count = 0
        self.active_count = 0
        self.max_active_count = 0

    def answer(
        self,
        tutor_request: TutorRequest,
        chunk_writer: Callable[[str], None] | None = None,
    ) -> TutorResponse:
        del chunk_writer
        with self._lock:
            self.requests.append(tutor_request)
            self.request_count += 1
            self.active_count += 1
            self.max_active_count = max(self.max_active_count, self.active_count)
        try:
            if not self._release_event.wait(timeout=5.0):
                raise RuntimeError("blocking tutor was not released")
            return TutorResponse(
                text="slow response",
                topic_tags=("slow",),
                model="test-model",
                provider="test",
            )
        finally:
            with self._lock:
                self.active_count -= 1


def test_split_irc_text_keeps_short_message_intact() -> None:
    """Short IRC messages are not split."""
    assert split_irc_text("hello") == ["hello"]


async def test_connect_and_register_requires_successful_sasl() -> None:
    """The IRC client accepts prefixed AUTHENTICATE continuation lines."""
    transcript: list[str] = []
    server, port = await _start_fake_server(_successful_sasl_handler(transcript))
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(_irc_config(port), outbound_queue)

    try:
        connection = await client.connect_and_register()
        connection.writer.close()
        await connection.writer.wait_closed()
    finally:
        server.close()
        await server.wait_closed()

    expected_secret = base64.b64encode(b"\0bot-login\0secret").decode("ascii")
    assert transcript == [
        "CAP LS 302",
        "NICK maker-guide",
        "USER maker-guide 0 * :Kolam Makers Bot",
        "CAP REQ :sasl",
        "AUTHENTICATE PLAIN",
        f"AUTHENTICATE {expected_secret}",
        "CAP END",
        "JOIN #kolam",
    ]


async def test_connect_and_register_fails_when_sasl_is_unavailable() -> None:
    """The IRC client refuses to continue when SASL is not advertised."""
    server, port = await _start_fake_server(_missing_sasl_handler)
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(_irc_config(port), outbound_queue)

    try:
        with pytest.raises(IrcError):
            await client.connect_and_register()
    finally:
        server.close()
        await server.wait_closed()


async def test_connect_and_register_accepts_multiline_capability_sasl() -> None:
    """SASL may be advertised on a later CAP LS continuation line."""
    transcript: list[str] = []
    server, port = await _start_fake_server(_multiline_sasl_handler(transcript))
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(_irc_config(port), outbound_queue)

    try:
        connection = await client.connect_and_register()
        connection.writer.close()
        await connection.writer.wait_closed()
    finally:
        server.close()
        await server.wait_closed()

    expected_secret = base64.b64encode(b"\0bot-login\0secret").decode("ascii")
    assert transcript == [
        "CAP LS 302",
        "NICK maker-guide",
        "USER maker-guide 0 * :Kolam Makers Bot",
        "CAP REQ :sasl",
        "AUTHENTICATE PLAIN",
        f"AUTHENTICATE {expected_secret}",
        "CAP END",
        "JOIN #kolam",
    ]


async def test_connect_and_register_accepts_unprefixed_capability_sasl() -> None:
    """Some servers send CAP replies without a source prefix."""
    transcript: list[str] = []
    server, port = await _start_fake_server(_unprefixed_sasl_handler(transcript))
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(_irc_config(port), outbound_queue)

    try:
        connection = await client.connect_and_register()
        connection.writer.close()
        await connection.writer.wait_closed()
    finally:
        server.close()
        await server.wait_closed()

    expected_secret = base64.b64encode(b"\0bot-login\0secret").decode("ascii")
    assert transcript == [
        "CAP LS 302",
        "NICK maker-guide",
        "USER maker-guide 0 * :Kolam Makers Bot",
        "CAP REQ :sasl",
        "AUTHENTICATE PLAIN",
        f"AUTHENTICATE {expected_secret}",
        "CAP END",
        "JOIN #kolam",
    ]


async def test_connect_and_register_times_out_stalled_connection_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Connection establishment has an application-level timeout."""

    async def stalled_open_connection(
        host: str,
        port: int,
        *,
        ssl: object,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        assert host == "127.0.0.1"
        assert port == 6697
        assert ssl is None
        await asyncio.sleep(10.0)
        raise AssertionError("connection should have timed out")

    monkeypatch.setattr(asyncio, "open_connection", stalled_open_connection)
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(_irc_config(6697, connect_timeout_seconds=0.01), outbound_queue)

    with pytest.raises(IrcError, match="IRC connection timed out"):
        await client.connect_and_register()


async def test_run_once_replies_to_public_help_command(migrated_database_path: Path) -> None:
    """Public channel commands are routed through shared chat handling."""
    _write_learner(migrated_database_path)
    responses: list[str] = []
    server, port = await _start_fake_server(
        _chat_response_handler(":alice!user@example PRIVMSG #kolam :!help hello", responses),
    )
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(
        _irc_config(port),
        outbound_queue,
        options=IrcClientOptions(database_path=migrated_database_path),
    )

    try:
        with pytest.raises(IrcError):
            await client.run_once()
    finally:
        server.close()
        await server.wait_closed()

    assert responses == [
        f"PRIVMSG #kolam :{FREEFORM_TUTOR_DISABLED_TEXT}",
        "PRIVMSG alice :\x01VERSION\x01",
    ]


async def test_public_thank_command_is_recorded(migrated_database_path: Path) -> None:
    """Public thank commands reach the shared command handler."""
    _write_cohort_member(migrated_database_path, "alice")
    _write_cohort_member(migrated_database_path, "bob")
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(
        _irc_config(6697),
        outbound_queue,
        options=IrcClientOptions(database_path=migrated_database_path),
    )

    await client.handle_private_message(
        IrcPrivateMessage(
            sender="alice",
            target="#kolam",
            text="!thank bob Explained SSH permissions",
        ),
    )

    assert await outbound_queue.get() == IrcOutboundMessage(
        channel="#kolam",
        text="Thank-you recorded. bob earned 10 points.",
    )


async def test_public_thank_announcement_is_broadcast(migrated_database_path: Path) -> None:
    """A thank promotion sends the response and public tier announcement."""
    _write_cohort_member(migrated_database_path, "alice")
    _write_cohort_member(migrated_database_path, "bob")
    with connect_database(migrated_database_path) as database_connection:
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle="bob",
                course_id=CATALOG.course.id,
                amount=490,
                reason="test",
                related_type="test",
                related_id="before-thank",
                created_at="2026-07-19T08:00:00Z",
            ),
        )
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(
        _irc_config(6697),
        outbound_queue,
        options=IrcClientOptions(database_path=migrated_database_path),
    )

    await client.handle_private_message(
        IrcPrivateMessage(
            sender="alice",
            target="#kolam",
            text="!thank bob Explained SSH permissions",
        ),
    )

    assert await outbound_queue.get() == IrcOutboundMessage(
        channel="#kolam",
        text="Thank-you recorded. bob earned 10 points.",
    )
    assert await outbound_queue.get() == IrcOutboundMessage(
        channel="#kolam",
        text="bob became an apprentice",
    )


async def test_public_help_lists_thank_command(migrated_database_path: Path) -> None:
    """Bare public help documents the peer thank command."""
    _write_learner(migrated_database_path)
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(
        _irc_config(6697),
        outbound_queue,
        options=IrcClientOptions(database_path=migrated_database_path),
    )

    await client.handle_private_message(
        IrcPrivateMessage(sender="alice", target="#kolam", text="!help"),
    )

    assert "!thank nickname reason" in (await outbound_queue.get()).text


async def test_run_once_times_out_when_registered_connection_goes_silent() -> None:
    """A half-open IRC connection is bounded by the steady-state read timeout."""
    server, port = await _start_fake_server(_silent_after_registration_handler)
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(_irc_config(port, read_timeout_seconds=0.05), outbound_queue)

    try:
        with pytest.raises(IrcError, match="IRC read timed out"):
            await asyncio.wait_for(client.run_once(), timeout=1.0)
    finally:
        server.close()
        await server.wait_closed()


async def test_run_once_sends_quit_message_when_cancelled() -> None:
    """Graceful shutdown tells IRC users the bot will return."""
    transcript: list[str] = []
    joined_event = asyncio.Event()

    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            while line := await _read_client_line(reader):
                transcript.append(line)
                _write_basic_registration_response(writer, line)
                await writer.drain()
                if line == "JOIN #kolam":
                    joined_event.set()
        finally:
            writer.close()
            await writer.wait_closed()

    server, port = await _start_fake_server(handle_client)
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    task = asyncio.create_task(IrcClient(_irc_config(port), outbound_queue).run_once())

    try:
        await asyncio.wait_for(joined_event.wait(), timeout=1.0)
        await _cancel_task(task)
    finally:
        server.close()
        await server.wait_closed()

    assert transcript[-1] == "QUIT :Coming back soon!"


async def test_run_once_replies_to_private_message_sender(migrated_database_path: Path) -> None:
    """Private IRC messages are answered back to the sender."""
    _write_learner(migrated_database_path)
    responses: list[str] = []
    server, port = await _start_fake_server(
        _chat_response_handler(":alice!user@example PRIVMSG maker-guide :hello", responses),
    )
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(
        _irc_config(port),
        outbound_queue,
        options=IrcClientOptions(database_path=migrated_database_path),
    )

    try:
        with pytest.raises(IrcError):
            await client.run_once()
    finally:
        server.close()
        await server.wait_closed()

    assert responses == [
        f"PRIVMSG alice :{FREEFORM_TUTOR_DISABLED_TEXT}",
        "PRIVMSG alice :\x01VERSION\x01",
    ]


async def test_run_once_requests_and_records_irc_client_version(
    migrated_database_path: Path,
) -> None:
    """Handled IRC messages trigger internal client evidence collection."""
    _write_learner(migrated_database_path)
    responses: list[str] = []
    server, port = await _start_fake_server(
        _ctcp_version_handler(responses),
    )
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(
        _irc_config(port),
        outbound_queue,
        options=IrcClientOptions(database_path=migrated_database_path),
    )

    try:
        with pytest.raises(IrcError):
            await client.run_once()
    finally:
        server.close()
        await server.wait_closed()

    assert responses == [
        f"PRIVMSG alice :{FREEFORM_TUTOR_DISABLED_TEXT}",
        "PRIVMSG alice :\x01VERSION\x01",
        "PONG :server",
    ]
    with connect_database(migrated_database_path) as database_connection:
        events = list_recent_audit_events_by_type(
            database_connection,
            "irc_ctcp_version",
            "alice",
            "2026-01-01T00:00:00Z",
            10,
        )
    assert len(events) == 1
    assert events[0].payload == {"version": "WeeChat 4.4.0"}


async def test_run_once_records_and_announces_learner_course_channel_join(
    migrated_database_path: Path,
) -> None:
    """Joining the course channel records the objective and broadcasts its promotion."""
    _write_cohort_member(migrated_database_path, "alice")
    with connect_database(migrated_database_path) as database_connection:
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle="alice",
                course_id=CATALOG.course.id,
                amount=445,
                reason="test",
                related_type="test",
                related_id="before-irc-join",
                created_at="2026-07-18T08:00:00Z",
            ),
        )
    responses: list[str] = []
    server, port = await _start_fake_server(_channel_join_handler("#lf2607", responses))
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(
        replace(_irc_config(port), channels=("#lf2607",)),
        outbound_queue,
        options=IrcClientOptions(database_path=migrated_database_path),
    )

    try:
        with pytest.raises(IrcError):
            await client.run_once()
    finally:
        server.close()
        await server.wait_closed()

    with connect_database(migrated_database_path) as database_connection:
        events = list_recent_audit_events_by_type(
            database_connection,
            "irc_channel_joined",
            "alice",
            "2026-01-01T00:00:00Z",
            10,
        )
    assert len(events) == 1
    assert events[0].payload == {"channel": "#lf2607"}
    with connect_database(migrated_database_path) as database_connection:
        assert list_completed_objective_ids(
            database_connection,
            "alice",
            CATALOG.course.id,
            "S1",
        ) == frozenset({"join-course-irc"})
    assert responses == ["PRIVMSG #lf2607 :alice became an apprentice"]


async def test_run_once_pongs_while_channel_join_persistence_is_blocked(
    migrated_database_path: Path,
) -> None:
    """A slow evidence write cannot block IRC keepalive handling."""
    _write_learner(migrated_database_path)
    persistence_started_event = threading.Event()
    release_persistence_event = threading.Event()
    responses: list[str] = []
    server, port = await _start_fake_server(
        _channel_join_then_ping_handler(
            responses,
            persistence_started_event,
            release_persistence_event,
        ),
    )
    client = _BlockingEvidenceIrcClient(
        _irc_config(port),
        asyncio.Queue(),
        persistence_started_event,
        release_persistence_event,
        IrcClientOptions(database_path=migrated_database_path),
    )

    try:
        with pytest.raises(IrcError):
            await client.run_once()
    finally:
        release_persistence_event.set()
        server.close()
        await server.wait_closed()

    assert responses == ["PONG :server"]


async def test_run_once_retries_check_after_irc_client_version(
    migrated_database_path: Path,
) -> None:
    """IRC check waits for terminal-client evidence instead of showing a failed check."""
    _write_terminal_irc_quest(migrated_database_path)
    responses: list[str] = []
    server, port = await _start_fake_server(
        _ctcp_check_retry_handler(responses),
    )
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(
        _irc_config(port),
        outbound_queue,
        options=IrcClientOptions(database_path=migrated_database_path),
    )

    try:
        with pytest.raises(IrcError):
            await client.run_once()
    finally:
        server.close()
        await server.wait_closed()

    assert responses[0] == "PRIVMSG alice :\x01VERSION\x01"
    assert responses[1].startswith("PRIVMSG alice :Done.")
    assert all("Not yet." not in response for response in responses)


async def test_run_once_pongs_while_slow_tutor_requests_are_bounded(
    migrated_database_path: Path,
) -> None:
    """Slow private tutor work does not block IRC PING handling."""
    _write_learner(migrated_database_path)
    release_event = threading.Event()
    tutor_client = _BlockingTutorClient(release_event)
    responses: list[str] = []
    server, port = await _start_fake_server(_slow_tutor_then_ping_handler(responses, release_event))
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(
        _irc_config(port, chat_worker_count=1, chat_queue_size=4),
        outbound_queue,
        options=IrcClientOptions(
            database_path=migrated_database_path,
            tutor_client=tutor_client,
        ),
    )

    try:
        with pytest.raises(IrcError):
            await client.run_once()
    finally:
        release_event.set()
        server.close()
        await server.wait_closed()

    assert responses == [
        "PONG :server",
        "PRIVMSG alice :slow response",
        "PRIVMSG alice :\x01VERSION\x01",
        "PRIVMSG alice :slow response",
    ]
    assert tutor_client.request_count == 2
    assert [request.message for request in tutor_client.requests] == [
        "first slow tutor",
        "second slow tutor",
    ]
    assert tutor_client.max_active_count == 1


@pytest.mark.parametrize("text", ["hello", "!today", "!check"])
async def test_public_channel_message_without_command_is_ignored(
    migrated_database_path: Path,
    text: str,
) -> None:
    """Public IRC chatter does not trigger the bot unless it is gated."""
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(
        _irc_config(0),
        outbound_queue,
        options=IrcClientOptions(database_path=migrated_database_path),
    )

    await client.handle_private_message(
        IrcPrivateMessage(sender="alice", target="#kolam", text=text),
    )

    assert outbound_queue.empty()


@pytest.mark.parametrize(
    ("private_message", "expected_visibility"),
    [
        (
            IrcPrivateMessage(sender="mallory", target="#kolam", text="!help secret words"),
            "public",
        ),
        (
            IrcPrivateMessage(sender="mallory", target="maker-guide", text="today secret words"),
            "private",
        ),
    ],
)
async def test_unknown_irc_sender_is_ignored_without_leaking_message_text(
    migrated_database_path: Path,
    caplog: pytest.LogCaptureFixture,
    private_message: IrcPrivateMessage,
    expected_visibility: str,
) -> None:
    """Unknown IRC senders are logged by metadata and do not get a response."""
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(
        _irc_config(0),
        outbound_queue,
        options=IrcClientOptions(database_path=migrated_database_path),
    )
    caplog.set_level("INFO", logger="maker_guide.irc")

    await client.handle_private_message(private_message)

    assert outbound_queue.empty()
    assert "ignored IRC message from unknown learner" in caplog.text
    assert "sender=mallory" in caplog.text
    assert f"visibility={expected_visibility}" in caplog.text
    assert "secret words" not in caplog.text


async def test_unknown_irc_sender_does_not_stop_reader_ping_handling(
    migrated_database_path: Path,
) -> None:
    """A bad sender cannot kill the IRC reader before later PING handling."""
    responses: list[str] = []
    server, port = await _start_fake_server(_unknown_sender_then_ping_handler(responses))
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(
        _irc_config(port),
        outbound_queue,
        options=IrcClientOptions(database_path=migrated_database_path),
    )

    try:
        with pytest.raises(IrcError):
            await client.run_once()
    finally:
        server.close()
        await server.wait_closed()

    assert responses == ["PONG :server"]


async def test_malformed_irc_event_log_does_not_leak_trailing_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Malformed IRC lines are logged without private trailing text."""
    server, port = await _start_fake_server(_malformed_private_text_handler)
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(_irc_config(port), outbound_queue)
    caplog.set_level("INFO", logger="maker_guide.irc")

    try:
        with pytest.raises(IrcError):
            await client.run_once()
    finally:
        server.close()
        await server.wait_closed()

    assert "irc event: PRIVMSG maker-guide" in caplog.text
    assert "secret words" not in caplog.text


async def test_chat_error_does_not_stop_reader_ping_handling() -> None:
    """Chat precondition failures are isolated to the current IRC message."""
    responses: list[str] = []
    server, port = await _start_fake_server(_unknown_sender_then_ping_handler(responses))
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = _ChatErrorIrcClient(_irc_config(port), outbound_queue)

    try:
        with pytest.raises(IrcError):
            await client.run_once()
    finally:
        server.close()
        await server.wait_closed()

    assert responses == ["PONG :server"]


@pytest.mark.parametrize("client_type", [_SqliteErrorIrcClient, _TutorErrorIrcClient])
async def test_operational_chat_errors_do_not_stop_reader_ping_handling(
    client_type: type[IrcClient],
) -> None:
    """Operational chat failures are isolated to the current IRC message."""
    responses: list[str] = []
    server, port = await _start_fake_server(_unknown_sender_then_ping_handler(responses))
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = client_type(_irc_config(port), outbound_queue)

    try:
        with pytest.raises(IrcError):
            await client.run_once()
    finally:
        server.close()
        await server.wait_closed()

    assert responses == ["PONG :server"]


async def test_public_channel_direct_mention_is_routed(
    migrated_database_path: Path,
) -> None:
    """Direct bot mentions in public IRC are routed after mention stripping."""
    _write_learner(migrated_database_path)
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(
        _irc_config(0),
        outbound_queue,
        options=IrcClientOptions(database_path=migrated_database_path),
    )

    await client.handle_private_message(
        IrcPrivateMessage(sender="alice", target="#kolam", text="maker-guide: hello"),
    )

    assert await outbound_queue.get() == IrcOutboundMessage(
        channel="#kolam",
        text=FREEFORM_TUTOR_DISABLED_TEXT,
    )


async def test_private_oversized_message_is_rejected_without_storage(
    migrated_database_path: Path,
) -> None:
    """Known private IRC oversized input gets a concise response and no storage."""
    _write_learner(migrated_database_path)
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(
        _irc_config(0),
        outbound_queue,
        options=IrcClientOptions(database_path=migrated_database_path),
    )

    await client.handle_private_message(
        IrcPrivateMessage(
            sender="alice",
            target="maker-guide",
            text="x" * (DEFAULT_CHAT_MAX_INPUT_CHARS + 1),
        ),
    )

    assert await outbound_queue.get() == IrcOutboundMessage(
        channel="alice",
        text=CHAT_INPUT_TOO_LONG_TEXT,
    )
    with connect_database(migrated_database_path) as database_connection:
        assert list_recent_help_interactions(database_connection, "alice", 10) == []


async def test_public_oversized_help_message_is_rejected_without_storage(
    migrated_database_path: Path,
) -> None:
    """Known public IRC oversized input gets a concise response and no storage."""
    _write_learner(migrated_database_path)
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = IrcClient(
        _irc_config(0),
        outbound_queue,
        options=IrcClientOptions(database_path=migrated_database_path),
    )

    await client.handle_private_message(
        IrcPrivateMessage(
            sender="alice",
            target="#kolam",
            text=f"!help {'x' * (DEFAULT_CHAT_MAX_INPUT_CHARS + 1)}",
        ),
    )

    assert await outbound_queue.get() == IrcOutboundMessage(
        channel="#kolam",
        text=CHAT_INPUT_TOO_LONG_TEXT,
    )
    with connect_database(migrated_database_path) as database_connection:
        assert list_recent_help_interactions(database_connection, "alice", 10) == []


async def test_sender_loop_acknowledges_after_successful_send() -> None:
    """Outbound queue items are acknowledged after all text is sent."""
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = _SenderLoopIrcClient(_irc_config(0), outbound_queue)
    writer = _RecordingWriter()
    await outbound_queue.put(IrcOutboundMessage(channel="#kolam", text="hello"))

    sender_task = asyncio.create_task(
        client.run_sender_loop(cast("asyncio.StreamWriter", writer)),
    )
    try:
        await asyncio.wait_for(outbound_queue.join(), timeout=1.0)
    finally:
        await _cancel_task(sender_task)

    assert writer.lines == ["PRIVMSG #kolam :hello\r\n"]


@pytest.mark.parametrize(
    ("text", "expected_lines"),
    [
        (
            "line one\nline two",
            [
                "PRIVMSG #kolam :line one\r\n",
                "PRIVMSG #kolam :line two\r\n",
            ],
        ),
        (
            "hello\r\nPRIVMSG #ops :owned\nbye",
            [
                "PRIVMSG #kolam :hello\r\n",
                "PRIVMSG #kolam :PRIVMSG #ops :owned\r\n",
                "PRIVMSG #kolam :bye\r\n",
            ],
        ),
    ],
)
async def test_sender_loop_splits_outbound_newlines_into_safe_privmsgs(
    text: str,
    expected_lines: list[str],
) -> None:
    """Response text cannot inject raw IRC command lines through CR/LF framing."""
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = _SenderLoopIrcClient(_irc_config(0), outbound_queue)
    writer = _RecordingWriter()
    await outbound_queue.put(IrcOutboundMessage(channel="#kolam", text=text))

    sender_task = asyncio.create_task(
        client.run_sender_loop(cast("asyncio.StreamWriter", writer)),
    )
    try:
        await asyncio.wait_for(outbound_queue.join(), timeout=1.0)
    finally:
        await _cancel_task(sender_task)

    assert writer.lines == expected_lines


async def test_sender_loop_requeues_message_when_send_fails() -> None:
    """Outbound messages are not silently lost when writer drain fails."""
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = _SenderLoopIrcClient(_irc_config(0), outbound_queue)
    outbound_message = IrcOutboundMessage(channel="#kolam", text="hello")
    await outbound_queue.put(outbound_message)

    with pytest.raises(OSError, match="synthetic send failure"):
        await client.run_sender_loop(
            cast("asyncio.StreamWriter", _RecordingWriter(fail_on_drain=True)),
        )

    assert await outbound_queue.get() == outbound_message
    outbound_queue.task_done()
    await asyncio.wait_for(outbound_queue.join(), timeout=1.0)


async def test_sender_loop_requeues_dequeued_message_when_cancelled() -> None:
    """Reconnect cancellation during transport drain does not drop an outbound message."""
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    client = _SenderLoopIrcClient(
        replace(_irc_config(0), outbound_interval_seconds=10.0),
        outbound_queue,
    )
    blocked_drain_started_event = asyncio.Event()
    writer = _RecordingWriter(blocked_drain_started_event=blocked_drain_started_event)
    outbound_message = IrcOutboundMessage(channel="#kolam", text="line one\nline two")
    await outbound_queue.put(outbound_message)

    sender_task = asyncio.create_task(
        client.run_sender_loop(cast("asyncio.StreamWriter", writer)),
    )
    await asyncio.wait_for(blocked_drain_started_event.wait(), timeout=1.0)
    await _cancel_task(sender_task)

    assert writer.lines == [
        "PRIVMSG #kolam :line one\r\n",
        "PRIVMSG #kolam :line two\r\n",
    ]
    assert await outbound_queue.get() == outbound_message
    outbound_queue.task_done()
    await asyncio.wait_for(outbound_queue.join(), timeout=1.0)


async def _start_fake_server(handler: ServerHandler) -> tuple[asyncio.Server, int]:
    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    sockets = server.sockets
    socket_name = cast("object", sockets[0].getsockname())
    if not isinstance(socket_name, tuple) or not isinstance(socket_name[1], int):
        raise RuntimeError("fake server did not bind a TCP port")
    return server, socket_name[1]


async def _cancel_task(task: asyncio.Task[None]) -> None:
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


def _irc_config(
    port: int,
    *,
    chat_worker_count: int = 1,
    chat_queue_size: int = 100,
    connect_timeout_seconds: float = 10.0,
    read_timeout_seconds: float = 300.0,
) -> IrcConfig:
    return IrcConfig(
        server="127.0.0.1",
        port=port,
        tls=False,
        nickname="maker-guide",
        username="maker-guide",
        realname="Kolam Makers Bot",
        channels=("#kolam",),
        sasl=SaslConfig(username="bot-login", password="secret"),
        connect_timeout_seconds=connect_timeout_seconds,
        registration_timeout_seconds=1.0,
        read_timeout_seconds=read_timeout_seconds,
        outbound_interval_seconds=0.0,
        chat_worker_count=chat_worker_count,
        chat_queue_size=chat_queue_size,
    )


def _write_learner(database_path: Path) -> None:
    with connect_database(database_path) as database_connection:
        upsert_learner(
            database_connection,
            Learner(
                handle="alice",
                joined_at="2026-07-18T09:00:00Z",
                tagline=None,
                created_at="2026-07-18T09:00:00Z",
            ),
        )


def _write_cohort_member(database_path: Path, handle: str) -> None:
    with connect_database(database_path) as database_connection:
        upsert_learner(
            database_connection,
            Learner(
                handle=handle,
                joined_at="2026-07-18T09:00:00Z",
                tagline=None,
                created_at="2026-07-18T09:00:00Z",
            ),
        )
        upsert_membership(
            database_connection,
            CohortMembership(
                handle=handle,
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


def _write_terminal_irc_quest(database_path: Path) -> None:
    with connect_database(database_path) as database_connection:
        upsert_learner(
            database_connection,
            Learner(
                handle="alice",
                joined_at="2026-07-18T09:00:00Z",
                tagline=None,
                created_at="2026-07-18T09:00:00Z",
            ),
        )
        upsert_membership(
            database_connection,
            CohortMembership(
                handle="alice",
                course_id="lf2607",
                joined_at="2026-07-18T09:00:00Z",
            ),
        )
        upsert_course_release(
            database_connection,
            CourseRelease(
                course_id="lf2607",
                session_reached="S9",
                released_at="2026-07-18T09:00:00Z",
            ),
        )
        for session in CATALOG.sessions_through("S9"):
            for objective in session.objectives:
                complete_session_objective(
                    database_connection,
                    SessionObjectiveCompletion(
                        handle="alice",
                        course_id="lf2607",
                        session_id=session.id,
                        objective_id=objective.id,
                        completed_at="2026-01-01T00:00:00Z",
                        evidence_json="{}",
                    ),
                )
        for quest in CATALOG.quests_available_through("S9"):
            if quest.id != "use-terminal-irc":
                complete_quest_repository(
                    database_connection,
                    QuestCompletion(
                        handle="alice",
                        course_id="lf2607",
                        quest_id=quest.id,
                        attempt_id=None,
                        completed_at="2026-01-01T00:00:00Z",
                        source="test",
                    ),
                )
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle="alice",
                course_id="lf2607",
                quest_id="use-terminal-irc",
                assigned_at="2026-01-01T00:00:00Z",
                source="test",
            ),
        )


def _successful_sasl_handler(transcript: list[str]) -> ServerHandler:
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            line = await _read_client_line(reader)
            if not line:
                break
            transcript.append(line)
            if line == "CAP LS 302":
                _write_server_line(writer, ":server CAP * LS :sasl")
            elif line == "CAP REQ :sasl":
                _write_server_line(writer, ":server CAP * ACK :sasl")
            elif line == "AUTHENTICATE PLAIN":
                _write_server_line(writer, ":server AUTHENTICATE +")
            elif line.startswith("AUTHENTICATE "):
                _write_server_line(writer, ":server 903 maker-guide :SASL successful")
            elif line == "CAP END":
                _write_server_line(writer, ":server 001 maker-guide :Welcome")
            elif line == "JOIN #kolam":
                break
            await writer.drain()
        writer.close()
        await writer.wait_closed()

    return handle_client


def _multiline_sasl_handler(transcript: list[str]) -> ServerHandler:
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            line = await _read_client_line(reader)
            if not line:
                break
            transcript.append(line)
            if line == "CAP LS 302":
                _write_server_line(writer, ":server CAP * LS * :multi-prefix")
                _write_server_line(writer, ":server CAP * LS :sasl")
            elif line == "CAP REQ :sasl":
                _write_server_line(writer, ":server CAP * ACK :sasl")
            elif line == "AUTHENTICATE PLAIN":
                _write_server_line(writer, "AUTHENTICATE +")
            elif line.startswith("AUTHENTICATE "):
                _write_server_line(writer, ":server 903 maker-guide :SASL successful")
            elif line == "CAP END":
                _write_server_line(writer, ":server 001 maker-guide :Welcome")
            elif line == "JOIN #kolam":
                break
            await writer.drain()
        writer.close()
        await writer.wait_closed()

    return handle_client


def _unprefixed_sasl_handler(transcript: list[str]) -> ServerHandler:
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            line = await _read_client_line(reader)
            if not line:
                break
            transcript.append(line)
            if line == "CAP LS 302":
                _write_server_line(writer, "CAP * LS :sasl=PLAIN")
            elif line == "CAP REQ :sasl":
                _write_server_line(writer, "CAP * ACK :sasl")
            elif line == "AUTHENTICATE PLAIN":
                _write_server_line(writer, "AUTHENTICATE +")
            elif line.startswith("AUTHENTICATE "):
                _write_server_line(writer, ":server 903 maker-guide :SASL successful")
            elif line == "CAP END":
                _write_server_line(writer, ":server 001 maker-guide :Welcome")
            elif line == "JOIN #kolam":
                break
            await writer.drain()
        writer.close()
        await writer.wait_closed()

    return handle_client


def _chat_response_handler(server_message: str, responses: list[str]) -> ServerHandler:
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            line = await _read_client_line(reader)
            if not line:
                break
            if line == "JOIN #kolam":
                _write_server_line(writer, server_message)
                await writer.drain()
                for response_number in range(2):
                    try:
                        responses.append(
                            await asyncio.wait_for(_read_client_line(reader), timeout=1.0),
                        )
                    except TimeoutError:
                        responses.append(f"timeout waiting for response {response_number}")
                break
            _write_basic_registration_response(writer, line)
            await writer.drain()
        writer.close()
        await writer.wait_closed()

    return handle_client


def _channel_join_handler(channel: str, responses: list[str]) -> ServerHandler:
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            line = await _read_client_line(reader)
            if not line:
                break
            if line == f"JOIN {channel}":
                _write_server_line(writer, f":alice!user@example JOIN :{channel}")
                await writer.drain()
                responses.append(await asyncio.wait_for(_read_client_line(reader), timeout=1.0))
                break
            _write_basic_registration_response(writer, line)
            await writer.drain()
        writer.close()
        await writer.wait_closed()

    return handle_client


def _channel_join_then_ping_handler(
    responses: list[str],
    persistence_started_event: threading.Event,
    release_persistence_event: threading.Event,
) -> ServerHandler:
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            line = await _read_client_line(reader)
            if not line:
                break
            if line == "JOIN #kolam":
                _write_server_line(writer, ":alice!user@example JOIN :#kolam")
                await writer.drain()
                await asyncio.to_thread(persistence_started_event.wait, 1.0)
                _write_server_line(writer, "PING :server")
                await writer.drain()
                responses.append(await asyncio.wait_for(_read_client_line(reader), timeout=1.0))
                release_persistence_event.set()
                break
            _write_basic_registration_response(writer, line)
            await writer.drain()
        writer.close()
        await writer.wait_closed()

    return handle_client


def _ctcp_version_handler(responses: list[str]) -> ServerHandler:
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            line = await _read_client_line(reader)
            if not line:
                break
            if line == "JOIN #kolam":
                _write_server_line(writer, ":alice!user@example PRIVMSG maker-guide :hello")
                await writer.drain()
                responses.append(await asyncio.wait_for(_read_client_line(reader), timeout=1.0))
                _write_server_line(
                    writer,
                    ":alice!user@example PRIVMSG maker-guide :\x01VERSION WeeChat 4.4.0\x01",
                )
                await writer.drain()
                responses.append(await asyncio.wait_for(_read_client_line(reader), timeout=1.0))
                _write_server_line(writer, "PING :server")
                await writer.drain()
                responses.append(await asyncio.wait_for(_read_client_line(reader), timeout=1.0))
                break
            _write_basic_registration_response(writer, line)
            await writer.drain()
        writer.close()
        await writer.wait_closed()

    return handle_client


def _ctcp_check_retry_handler(responses: list[str]) -> ServerHandler:
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            line = await _read_client_line(reader)
            if not line:
                break
            if line == "JOIN #kolam":
                _write_server_line(writer, ":alice!user@example PRIVMSG maker-guide :check")
                await writer.drain()
                responses.append(await asyncio.wait_for(_read_client_line(reader), timeout=1.0))
                _write_server_line(
                    writer,
                    ":alice!user@example PRIVMSG maker-guide :\x01VERSION WeeChat 4.4.0\x01",
                )
                await writer.drain()
                while True:
                    try:
                        responses.append(
                            await asyncio.wait_for(_read_client_line(reader), timeout=0.2),
                        )
                    except TimeoutError:
                        break
                break
            _write_basic_registration_response(writer, line)
            await writer.drain()
        writer.close()
        await writer.wait_closed()

    return handle_client


async def _silent_after_registration_handler(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    while True:
        line = await _read_client_line(reader)
        if not line:
            break
        if line == "JOIN #kolam":
            await reader.read()
            break
        _write_basic_registration_response(writer, line)
        await writer.drain()
    writer.close()
    await writer.wait_closed()


def _slow_tutor_then_ping_handler(
    responses: list[str],
    release_event: threading.Event,
) -> ServerHandler:
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            line = await _read_client_line(reader)
            if not line:
                break
            if line == "JOIN #kolam":
                _write_server_line(
                    writer,
                    ":alice!user@example PRIVMSG maker-guide :first slow tutor",
                )
                _write_server_line(
                    writer,
                    ":alice!user@example PRIVMSG maker-guide :second slow tutor",
                )
                _write_server_line(writer, "PING :server")
                await writer.drain()
                try:
                    responses.append(await asyncio.wait_for(_read_client_line(reader), timeout=1.0))
                except TimeoutError:
                    responses.append("timeout waiting for pong")
                    release_event.set()
                    break
                release_event.set()
                for response_number in range(3):
                    try:
                        responses.append(
                            await asyncio.wait_for(_read_client_line(reader), timeout=1.0),
                        )
                    except TimeoutError:
                        responses.append(f"timeout waiting for response {response_number}")
                break
            _write_basic_registration_response(writer, line)
            await writer.drain()
        writer.close()
        await writer.wait_closed()

    return handle_client


def _unknown_sender_then_ping_handler(responses: list[str]) -> ServerHandler:
    async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            line = await _read_client_line(reader)
            if not line:
                break
            if line == "JOIN #kolam":
                _write_server_line(writer, ":mallory!user@example PRIVMSG #kolam :!help")
                _write_server_line(writer, "PING :server")
                await writer.drain()
                try:
                    responses.append(await asyncio.wait_for(_read_client_line(reader), timeout=1.0))
                except TimeoutError:
                    responses.append("timeout")
                break
            _write_basic_registration_response(writer, line)
            await writer.drain()
        writer.close()
        await writer.wait_closed()

    return handle_client


async def _malformed_private_text_handler(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    while True:
        line = await _read_client_line(reader)
        if not line:
            break
        if line == "JOIN #kolam":
            _write_server_line(writer, "PRIVMSG maker-guide :secret words")
            await writer.drain()
            break
        _write_basic_registration_response(writer, line)
        await writer.drain()
    writer.close()
    await writer.wait_closed()


def _write_basic_registration_response(writer: asyncio.StreamWriter, line: str) -> None:
    if line == "CAP LS 302":
        _write_server_line(writer, ":server CAP * LS :sasl")
    elif line == "CAP REQ :sasl":
        _write_server_line(writer, ":server CAP * ACK :sasl")
    elif line == "AUTHENTICATE PLAIN":
        _write_server_line(writer, "AUTHENTICATE +")
    elif line.startswith("AUTHENTICATE "):
        _write_server_line(writer, ":server 903 maker-guide :SASL successful")
    elif line == "CAP END":
        _write_server_line(writer, ":server 001 maker-guide :Welcome")


async def _missing_sasl_handler(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    line = await _read_client_line(reader)
    if line == "CAP LS 302":
        _write_server_line(writer, ":server CAP * LS :multi-prefix")
        await writer.drain()
    writer.close()
    await writer.wait_closed()


async def _read_client_line(reader: asyncio.StreamReader) -> str:
    line = await reader.readline()
    return line.decode("utf-8").rstrip("\r\n")


def _write_server_line(writer: asyncio.StreamWriter, line: str) -> None:
    writer.write(f"{line}\r\n".encode())
