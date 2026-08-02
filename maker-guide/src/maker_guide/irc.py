"""Async IRC client with mandatory SASL authentication."""

from __future__ import annotations

import asyncio
import base64
import logging
import random
import sqlite3
import ssl
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from maker_guide.chat.contract import (
    ChatDependencies,
    ChatError,
    ChatRequest,
    IrcChatContext,
    UnknownLearnerError,
)
from maker_guide.chat.presenter import format_tier_promotion_announcements
from maker_guide.chat.service import handle_chat_request
from maker_guide.config import IrcConfig
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG
from maker_guide.curriculum.models import CourseCatalog
from maker_guide.events import IrcOutboundMessage
from maker_guide.llm_tutor import (
    DEFAULT_TUTOR_MAX_TOKENS,
    AnswerInterpreter,
    TutorClient,
    TutorError,
)
from maker_guide.progress.service import complete_session_objective, current_session_objective
from maker_guide.repositories.audit_event import AuditEvent, append_audit_event
from maker_guide.repositories.cohort_membership import get_membership
from maker_guide.repositories.course_release import get_course_release
from maker_guide.repositories.helpers import connect_database, transaction
from maker_guide.repositories.learner import get_learner

LOGGER = logging.getLogger(__name__)
IRC_LINE_ENDING = "\r\n"
MAX_IRC_TEXT_BYTES = 390
CAPABILITY_CONTINUATION_MARKER = "*"
CTCP_DELIMITER = "\x01"


class IrcError(RuntimeError):
    """Raised for IRC protocol or authentication failures."""


@dataclass(frozen=True, kw_only=True, slots=True)
class IrcConnection:
    """Registered IRC connection streams."""

    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter


@dataclass(frozen=True, kw_only=True, slots=True)
class IrcPrivateMessage:
    """Parsed IRC PRIVMSG command."""

    sender: str
    target: str
    text: str


@dataclass(frozen=True, kw_only=True, slots=True)
class _StopChatWorker:
    """Sentinel that asks a connection-scoped IRC chat worker to exit."""


@dataclass(frozen=True, kw_only=True, slots=True)
class _IrcEvidence:
    """One IRC observation to persist without delaying socket reads."""

    event_type: Literal["irc_channel_joined", "irc_ctcp_version"]
    handle: str
    payload: dict[str, object]
    retry_message: IrcPrivateMessage | None = None


@dataclass(frozen=True, kw_only=True, slots=True)
class _StopEvidenceWorker:
    """Sentinel that asks a connection-scoped IRC evidence worker to exit."""


@dataclass(frozen=True, kw_only=True, slots=True)
class _IrcChatResult:
    """IRC outbound message plus transport-specific retry metadata."""

    outbound_message: IrcOutboundMessage | None
    retry_after_irc_client_verification: bool = False
    public_announcements: tuple[str, ...] = ()


type _ChatQueueItem = IrcPrivateMessage | _StopChatWorker
type _EvidenceQueueItem = _IrcEvidence | _StopEvidenceWorker
_STOP_CHAT_WORKER = _StopChatWorker()
_STOP_EVIDENCE_WORKER = _StopEvidenceWorker()
_CHAT_WORKER_OPERATIONAL_ERRORS = (ChatError, TutorError, sqlite3.Error, OSError, TimeoutError)


@dataclass(frozen=True, kw_only=True, slots=True)
class IrcClientOptions:
    """Optional runtime dependencies for IRC chat handling."""

    database_path: Path | None = None
    """SQLite path used when IRC messages need shared chat handling."""
    catalog: CourseCatalog = DEFAULT_CATALOG
    """Course catalog used for deterministic progress responses."""
    tutor_client: TutorClient | None = None
    """Optional read-only LLM tutor for private fallback help."""
    answer_interpreter: AnswerInterpreter | None = None
    """Optional semantic interpreter for private learner answers."""
    tutor_max_tokens: int = DEFAULT_TUTOR_MAX_TOKENS
    """Maximum tokens to request from the tutor provider."""


async def enqueue_public_announcements(
    outbound_queue: asyncio.Queue[IrcOutboundMessage],
    channels: tuple[str, ...],
    announcements: tuple[str, ...],
) -> None:
    """Queue each public announcement for every configured IRC channel."""
    for announcement in announcements:
        for channel in channels:
            await outbound_queue.put(IrcOutboundMessage(channel=channel, text=announcement))


class IrcClient:
    """Async IRC client that requires SASL before joining channels."""

    def __init__(
        self,
        configuration: IrcConfig,
        outbound_queue: asyncio.Queue[IrcOutboundMessage],
        options: IrcClientOptions | None = None,
    ) -> None:
        client_options = IrcClientOptions() if options is None else options
        if configuration.chat_worker_count <= 0:
            raise ValueError("IRC chat worker count must be positive")
        if configuration.chat_queue_size <= 0:
            raise ValueError("IRC chat queue size must be positive")
        self._config = configuration
        self._outbound_queue = outbound_queue
        self._database_path = client_options.database_path
        self._catalog = client_options.catalog
        self._tutor_client = client_options.tutor_client
        self._answer_interpreter = client_options.answer_interpreter
        self._tutor_max_tokens = client_options.tutor_max_tokens
        self._active_connection_token: object | None = None
        self._ctcp_version_requested: set[str] = set()
        self._pending_ctcp_retry_messages: dict[str, IrcPrivateMessage] = {}

    async def run_forever(self) -> None:
        """Reconnect forever with bounded exponential backoff."""
        reconnect_delay_seconds = self._config.reconnect_initial_seconds
        while True:
            try:
                await self.run_once()
                reconnect_delay_seconds = self._config.reconnect_initial_seconds
            except asyncio.CancelledError:
                raise
            except IrcError as error:
                LOGGER.error("IRC failure: %s", error)
            except TimeoutError as error:
                LOGGER.warning("IRC timeout: %s", error)
            except OSError as error:
                LOGGER.warning("IRC connection failure: %s", error)

            jitter_seconds = random.uniform(0.0, reconnect_delay_seconds / 4.0)
            await asyncio.sleep(reconnect_delay_seconds + jitter_seconds)
            reconnect_delay_seconds = min(
                reconnect_delay_seconds * 2.0,
                self._config.reconnect_max_seconds,
            )

    async def run_once(self) -> None:  # noqa: C901 - Connection lifecycle owns its task cleanup.
        """Connect, register, and run until the connection closes."""
        connection = await self.connect_and_register()
        connection_token = object()
        self._active_connection_token = connection_token
        chat_queue: asyncio.Queue[_ChatQueueItem] = asyncio.Queue(
            maxsize=self._config.chat_queue_size + self._config.chat_worker_count,
        )
        evidence_queue: asyncio.Queue[_EvidenceQueueItem] = asyncio.Queue(
            maxsize=self._config.chat_queue_size,
        )
        chat_worker_tasks: set[asyncio.Task[None]] = set()
        tasks: set[asyncio.Task[None]] = set()
        evidence_worker_task = asyncio.create_task(
            self._evidence_worker_loop(evidence_queue, chat_queue),
            name="irc-evidence-worker",
        )
        graceful_shutdown = False
        try:
            tasks.add(
                asyncio.create_task(
                    self._reader_loop(
                        connection.reader,
                        connection.writer,
                        chat_queue,
                        evidence_queue,
                    ),
                ),
            )
            tasks.add(asyncio.create_task(self._sender_loop(connection.writer)))
            for worker_number in range(self._config.chat_worker_count):
                chat_worker_task = asyncio.create_task(
                    self._chat_worker_loop(chat_queue, connection_token),
                    name=f"irc-chat-worker-{worker_number}",
                )
                chat_worker_tasks.add(chat_worker_task)
                tasks.add(chat_worker_task)
            finished_tasks, pending_tasks = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_EXCEPTION,
            )
            self._deactivate_connection(connection_token)
            for pending_task in pending_tasks - chat_worker_tasks:
                pending_task.cancel()
            await asyncio.gather(
                *(pending_tasks - chat_worker_tasks),
                return_exceptions=True,
            )
            await self._stop_evidence_worker(evidence_queue, evidence_worker_task)
            await self._stop_chat_workers(chat_queue, chat_worker_tasks)
            completed_tasks = finished_tasks | pending_tasks
            for completed_task in completed_tasks:
                if not completed_task.cancelled():
                    completed_task.result()
        except asyncio.CancelledError:
            graceful_shutdown = True
            raise
        finally:
            self._deactivate_connection(connection_token)
            for running_task in tasks:
                if not running_task.done():
                    running_task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if not evidence_worker_task.done():
                evidence_worker_task.cancel()
            await asyncio.gather(evidence_worker_task, return_exceptions=True)
            if graceful_shutdown:
                _write_line(connection.writer, "QUIT :Coming back soon!")
                try:
                    await connection.writer.drain()
                except OSError as error:
                    LOGGER.debug("ignored IRC quit failure: %s", error)
            await _close_writer(connection.writer)

    def _deactivate_connection(self, connection_token: object) -> None:
        if self._active_connection_token is connection_token:
            self._active_connection_token = None

    async def _stop_chat_workers(
        self,
        chat_queue: asyncio.Queue[_ChatQueueItem],
        chat_worker_tasks: set[asyncio.Task[None]],
    ) -> None:
        active_chat_worker_tasks = {
            chat_worker_task
            for chat_worker_task in chat_worker_tasks
            if not chat_worker_task.done()
        }
        if not active_chat_worker_tasks:
            return
        self._discard_queued_chat_messages(chat_queue)
        for _chat_worker_task in active_chat_worker_tasks:
            chat_queue.put_nowait(_STOP_CHAT_WORKER)
        await asyncio.gather(*active_chat_worker_tasks, return_exceptions=True)

    async def _stop_evidence_worker(
        self,
        evidence_queue: asyncio.Queue[_EvidenceQueueItem],
        evidence_worker_task: asyncio.Task[None],
    ) -> None:
        await evidence_queue.join()
        evidence_queue.put_nowait(_STOP_EVIDENCE_WORKER)
        await evidence_worker_task

    def _discard_queued_chat_messages(self, chat_queue: asyncio.Queue[_ChatQueueItem]) -> None:
        discarded_count = 0
        while True:
            try:
                chat_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            chat_queue.task_done()
            discarded_count += 1
        if discarded_count:
            LOGGER.info("discarded queued IRC chat messages count=%s", discarded_count)

    async def connect_and_register(self) -> IrcConnection:
        """Open a TCP connection and complete mandatory SASL registration."""
        ssl_context = ssl.create_default_context() if self._config.tls else None
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    self._config.server,
                    self._config.port,
                    ssl=ssl_context,
                ),
                timeout=self._config.connect_timeout_seconds,
            )
        except TimeoutError as error:
            raise IrcError("IRC connection timed out") from error
        try:
            await self._register(reader, writer)
            for channel in self._config.channels:
                _write_line(writer, f"JOIN {channel}")
            await writer.drain()
        except BaseException:
            await _close_writer(writer)
            raise
        return IrcConnection(reader=reader, writer=writer)

    async def _register(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        if self._config.sasl.mechanism != "PLAIN":
            raise IrcError("only SASL PLAIN is supported")

        _write_line(writer, "CAP LS 302")
        _write_line(writer, f"NICK {self._config.nickname}")
        _write_line(writer, f"USER {self._config.username} 0 * :{self._config.realname}")
        await writer.drain()

        await self._expect_capability_sasl(reader, writer)
        _write_line(writer, "CAP REQ :sasl")
        await writer.drain()
        await self._expect_capability_ack(reader, writer)

        _write_line(writer, "AUTHENTICATE PLAIN")
        await writer.drain()
        await self._expect_authenticate_continue(reader, writer)

        secret = f"\0{self._config.sasl.username}\0{self._config.sasl.password}".encode()
        _write_line(writer, f"AUTHENTICATE {base64.b64encode(secret).decode('ascii')}")
        await writer.drain()
        await self._expect_sasl_success(reader, writer)

        _write_line(writer, "CAP END")
        await writer.drain()
        await self._expect_registered(reader, writer)

    async def _expect_capability_sasl(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        capability_tokens: set[str] = set()
        while True:
            line = await self._read_registration_line(reader, writer)
            if _cap_subcommand(line) == "ls":
                capability_tokens.update(_capability_tokens(line))
                if "sasl" in capability_tokens:
                    return
                if not _is_capability_continuation(line):
                    raise IrcError("IRC server does not advertise SASL")

    async def _expect_capability_ack(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        while True:
            line = await self._read_registration_line(reader, writer)
            if _cap_subcommand(line) == "ack" and "sasl" in _capability_tokens(line):
                return
            if _cap_subcommand(line) == "nak":
                raise IrcError("IRC server rejected SASL capability")

    async def _expect_authenticate_continue(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        while True:
            line = await self._read_registration_line(reader, writer)
            if _is_authenticate_continue(line):
                return

    async def _expect_sasl_success(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        while True:
            line = await self._read_registration_line(reader, writer)
            numeric = _numeric_reply(line)
            if numeric == "903":
                return
            if numeric in {"904", "905", "906", "907"}:
                raise IrcError(f"SASL authentication failed with reply {numeric}")

    async def _expect_registered(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        while True:
            line = await self._read_registration_line(reader, writer)
            if _numeric_reply(line) == "001":
                return

    async def _read_registration_line(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> str:
        try:
            line = await asyncio.wait_for(
                _read_line(reader),
                timeout=self._config.registration_timeout_seconds,
            )
        except TimeoutError as error:
            raise IrcError("IRC registration timed out waiting for server line") from error
        if not line:
            raise IrcError("IRC connection closed during registration")
        LOGGER.debug("irc registration event: %s", line)
        if line.startswith("PING "):
            _write_line(writer, f"PONG {line.removeprefix('PING ')}")
            await writer.drain()
        return line

    async def _reader_loop(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        chat_queue: asyncio.Queue[_ChatQueueItem],
        evidence_queue: asyncio.Queue[_EvidenceQueueItem],
    ) -> None:
        while True:
            try:
                line = await asyncio.wait_for(
                    _read_line(reader),
                    timeout=self._config.read_timeout_seconds,
                )
            except TimeoutError as error:
                raise IrcError("IRC read timed out waiting for server line") from error
            if not line:
                raise IrcError("IRC connection closed")
            if line.startswith("PING "):
                _write_line(writer, f"PONG {line.removeprefix('PING ')}")
                await writer.drain()
                continue
            self._enqueue_channel_join_evidence(line, evidence_queue)
            private_message = _private_message_from_line(line)
            if private_message is None:
                LOGGER.info("irc event: %s", _redacted_irc_event(line))
                continue
            if self._enqueue_ctcp_version_evidence(private_message, evidence_queue):
                continue
            self._enqueue_private_message(chat_queue, private_message)

    def _enqueue_channel_join_evidence(
        self,
        line: str,
        evidence_queue: asyncio.Queue[_EvidenceQueueItem],
    ) -> None:
        channel_join = _channel_join_from_line(line)
        if channel_join is None or self._database_path is None:
            return
        sender, channel = channel_join
        if sender.casefold() == self._config.nickname.casefold() or channel.casefold() not in {
            item.casefold() for item in self._config.channels
        }:
            return
        self._enqueue_evidence(
            evidence_queue,
            _IrcEvidence(
                event_type="irc_channel_joined",
                handle=sender,
                payload={"channel": channel},
            ),
        )

    def _enqueue_ctcp_version_evidence(
        self,
        private_message: IrcPrivateMessage,
        evidence_queue: asyncio.Queue[_EvidenceQueueItem],
    ) -> bool:
        version = _ctcp_version_response(private_message.text)
        if version is None:
            return False
        if private_message.target.casefold() != self._config.nickname.casefold():
            return True
        if self._database_path is None:
            LOGGER.debug(
                "ignored IRC client version response because no database is configured sender=%s",
                private_message.sender,
            )
            return True
        self._enqueue_evidence(
            evidence_queue,
            _IrcEvidence(
                event_type="irc_ctcp_version",
                handle=private_message.sender,
                payload={"version": version},
                retry_message=self._pending_ctcp_retry_messages.pop(
                    private_message.sender,
                    None,
                ),
            ),
        )
        return True

    def _enqueue_evidence(
        self,
        evidence_queue: asyncio.Queue[_EvidenceQueueItem],
        evidence: _IrcEvidence,
    ) -> None:
        try:
            evidence_queue.put_nowait(evidence)
        except asyncio.QueueFull:
            LOGGER.warning(
                "dropped IRC evidence because queue is full type=%s sender=%s",
                evidence.event_type,
                evidence.handle,
            )

    async def _evidence_worker_loop(
        self,
        evidence_queue: asyncio.Queue[_EvidenceQueueItem],
        chat_queue: asyncio.Queue[_ChatQueueItem],
    ) -> None:
        while True:
            queue_item = await evidence_queue.get()
            try:
                if isinstance(queue_item, _StopEvidenceWorker):
                    return
                public_announcements = await asyncio.to_thread(self._persist_evidence, queue_item)
                if public_announcements is not None:
                    await enqueue_public_announcements(
                        self._outbound_queue,
                        self._config.channels,
                        public_announcements,
                    )
                    if queue_item.retry_message is not None:
                        self._enqueue_private_message(chat_queue, queue_item.retry_message)
            finally:
                evidence_queue.task_done()

    def _persist_evidence(self, evidence: _IrcEvidence) -> tuple[str, ...] | None:
        if self._database_path is None:
            return None
        public_announcements: tuple[str, ...] = ()
        try:
            with connect_database(self._database_path) as database_connection:
                if get_learner(database_connection, evidence.handle) is None:
                    return None
                with transaction(database_connection):
                    created_at = _current_timestamp()
                    channel = evidence.payload.get("channel")
                    audit_event_id = append_audit_event(
                        database_connection,
                        AuditEvent(
                            event_type=evidence.event_type,
                            handle=evidence.handle,
                            source="irc",
                            created_at=created_at,
                            payload=evidence.payload,
                        ),
                    )
                    if (
                        evidence.event_type == "irc_channel_joined"
                        and isinstance(channel, str)
                        and channel.casefold() == "#lf2607"
                        and get_membership(
                            database_connection,
                            evidence.handle,
                            self._catalog.course.id,
                        )
                        is not None
                        and get_course_release(database_connection, self._catalog.course.id)
                        is not None
                    ):
                        current_objective_result = current_session_objective(
                            database_connection,
                            self._catalog,
                            handle=evidence.handle,
                        )
                        if (
                            current_objective_result.session_id == "S1"
                            and current_objective_result.objective is not None
                            and current_objective_result.objective.id == "join-course-irc"
                        ):
                            public_announcements = format_tier_promotion_announcements(
                                complete_session_objective(
                                    database_connection,
                                    self._catalog,
                                    handle=evidence.handle,
                                    session_id="S1",
                                    objective_id="join-course-irc",
                                    completed_at=created_at,
                                    evidence={
                                        "audit_event_id": audit_event_id,
                                        "channel": channel,
                                    },
                                    source="irc",
                                ).tier_promotions,
                            )
        except (OSError, sqlite3.Error) as error:
            LOGGER.warning(
                "could not persist IRC evidence type=%s sender=%s error=%s",
                evidence.event_type,
                evidence.handle,
                error.__class__.__name__,
            )
            return None
        return public_announcements

    def _should_request_ctcp_version(self, sender: str) -> bool:
        if sender in self._ctcp_version_requested:
            return False
        self._ctcp_version_requested.add(sender)
        return True

    def _enqueue_private_message(
        self,
        chat_queue: asyncio.Queue[_ChatQueueItem],
        private_message: IrcPrivateMessage,
    ) -> None:
        if not self._should_handle_private_message(private_message):
            return
        if chat_queue.qsize() >= self._config.chat_queue_size:
            LOGGER.warning(
                "dropped IRC chat message because queue is full sender=%s target=%s",
                private_message.sender,
                private_message.target,
            )
            return
        try:
            chat_queue.put_nowait(private_message)
        except asyncio.QueueFull:
            LOGGER.warning(
                "dropped IRC chat message because queue is full sender=%s target=%s",
                private_message.sender,
                private_message.target,
            )

    def _should_handle_private_message(self, private_message: IrcPrivateMessage) -> bool:
        if private_message.sender.casefold() == self._config.nickname.casefold():
            return False
        visibility = _message_visibility(private_message.target)
        return (
            _chat_text_from_irc_message(
                private_message,
                self._config.nickname,
                visibility,
            )
            is not None
        )

    async def _chat_worker_loop(
        self,
        chat_queue: asyncio.Queue[_ChatQueueItem],
        connection_token: object,
    ) -> None:
        while True:
            queue_item = await chat_queue.get()
            try:
                if isinstance(queue_item, _StopChatWorker):
                    return
                try:
                    await self.handle_private_message(queue_item, connection_token)
                except _CHAT_WORKER_OPERATIONAL_ERRORS as error:
                    LOGGER.warning(
                        "ignored IRC chat operational error sender=%s target=%s error=%s",
                        queue_item.sender,
                        queue_item.target,
                        error.__class__.__name__,
                    )
            finally:
                chat_queue.task_done()

    async def handle_private_message(
        self,
        private_message: IrcPrivateMessage,
        connection_token: object | None = None,
    ) -> None:
        """Handle one parsed IRC private message event."""
        if private_message.sender.casefold() == self._config.nickname.casefold():
            return

        visibility = _message_visibility(private_message.target)
        chat_text = _chat_text_from_irc_message(
            private_message,
            self._config.nickname,
            visibility,
        )
        if chat_text is None:
            return
        database_path = self._database_path
        if database_path is None:
            raise IrcError("IRC chat handling requires a database path")

        chat_context = IrcChatContext(
            nickname=private_message.sender,
            target=private_message.target,
            reply_target=_response_target(private_message, self._config.nickname),
        )
        chat_result = await asyncio.to_thread(
            self._outbound_message_for_chat,
            database_path,
            private_message,
            visibility,
            chat_text,
            chat_context,
        )
        if not self._is_current_connection(connection_token):
            return
        if chat_result.retry_after_irc_client_verification and self._should_request_ctcp_version(
            private_message.sender,
        ):
            self._pending_ctcp_retry_messages[private_message.sender] = private_message
            await self._outbound_queue.put(
                IrcOutboundMessage(
                    channel=private_message.sender,
                    text=f"{CTCP_DELIMITER}VERSION{CTCP_DELIMITER}",
                ),
            )
            return
        if chat_result.outbound_message is not None:
            await self._outbound_queue.put(chat_result.outbound_message)
            await enqueue_public_announcements(
                self._outbound_queue,
                self._config.channels,
                chat_result.public_announcements,
            )
            if self._should_request_ctcp_version(private_message.sender):
                await self._outbound_queue.put(
                    IrcOutboundMessage(
                        channel=private_message.sender,
                        text=f"{CTCP_DELIMITER}VERSION{CTCP_DELIMITER}",
                    ),
                )

    def _is_current_connection(self, connection_token: object | None) -> bool:
        return connection_token is None or self._active_connection_token is connection_token

    def _outbound_message_for_chat(
        self,
        database_path: Path,
        private_message: IrcPrivateMessage,
        visibility: Literal["public", "private"],
        chat_text: str,
        chat_context: IrcChatContext,
    ) -> _IrcChatResult:
        with connect_database(database_path) as database_connection:
            try:
                response = handle_chat_request(
                    ChatRequest(
                        context=chat_context,
                        visibility=visibility,
                        text=chat_text,
                    ),
                    ChatDependencies(
                        database_connection=database_connection,
                        catalog=self._catalog,
                        bot_name=self._config.nickname,
                        tutor_client=self._tutor_client,
                        answer_interpreter=self._answer_interpreter,
                        tutor_max_tokens=self._tutor_max_tokens,
                    ),
                )
            except UnknownLearnerError:
                LOGGER.info(
                    "ignored IRC message from unknown learner sender=%s target=%s visibility=%s",
                    private_message.sender,
                    private_message.target,
                    visibility,
                )
                return _IrcChatResult(outbound_message=None)
        if not response.text:
            return _IrcChatResult(outbound_message=None)
        return _IrcChatResult(
            outbound_message=IrcOutboundMessage(
                channel=chat_context.reply_target,
                text=response.text,
            ),
            retry_after_irc_client_verification=response.retry_after_irc_client_verification,
            public_announcements=response.public_announcements,
        )

    async def _sender_loop(self, writer: asyncio.StreamWriter) -> None:
        while True:
            outbound_message = await self._outbound_queue.get()
            try:
                await self._send_outbound_message(writer, outbound_message)
            except asyncio.CancelledError:
                self._requeue_failed_outbound_message(outbound_message)
                self._outbound_queue.task_done()
                raise
            except (OSError, TimeoutError):
                self._requeue_failed_outbound_message(outbound_message)
                self._outbound_queue.task_done()
                raise
            else:
                self._outbound_queue.task_done()
                await asyncio.sleep(self._config.outbound_interval_seconds)

    async def _send_outbound_message(
        self,
        writer: asyncio.StreamWriter,
        outbound_message: IrcOutboundMessage,
    ) -> None:
        for text_line in outbound_message.text.splitlines() or [""]:
            for text_part in split_irc_text(text_line):
                _write_line(writer, f"PRIVMSG {outbound_message.channel} :{text_part}")
        await writer.drain()

    def _requeue_failed_outbound_message(self, outbound_message: IrcOutboundMessage) -> None:
        try:
            self._outbound_queue.put_nowait(outbound_message)
        except asyncio.QueueFull:
            LOGGER.warning(
                "dropped outbound IRC message after send failure because queue is full channel=%s",
                outbound_message.channel,
            )


def split_irc_text(text: str) -> list[str]:
    """Split message text into safe IRC-sized chunks."""
    if not text:
        return [""]
    parts: list[str] = []
    remaining = text
    while remaining:
        encoded = remaining.encode("utf-8")
        if len(encoded) <= MAX_IRC_TEXT_BYTES:
            parts.append(remaining)
            break
        parts.append(encoded[:MAX_IRC_TEXT_BYTES].decode("utf-8", errors="ignore"))
        remaining = remaining[len(parts[-1]) :]
    return parts


def _private_message_from_line(line: str) -> IrcPrivateMessage | None:
    without_tags = line.partition(" ")[2] if line.startswith("@") else line
    prefix = ""
    body = without_tags
    if body.startswith(":"):
        prefix, _, body = body[1:].partition(" ")
        if not body:
            return None

    command, _, parameters = body.partition(" ")
    if command.casefold() != "privmsg" or not parameters:
        return None

    target, text = _private_message_target_and_text(parameters)
    # Deployment enforces that each IRC nickname equals its LLDAP username.
    sender = _nickname_from_prefix(prefix)
    if not sender or not target or not text:
        return None
    return IrcPrivateMessage(sender=sender, target=target, text=text)


def _channel_join_from_line(line: str) -> tuple[str, str] | None:
    without_tags = line.partition(" ")[2] if line.startswith("@") else line
    if not without_tags.startswith(":"):
        return None
    prefix, _, body = without_tags[1:].partition(" ")
    command, _, channel = body.partition(" ")
    sender = _nickname_from_prefix(prefix)
    channel = channel.removeprefix(":").split(maxsplit=1)[0]
    if command.casefold() != "join" or not sender or not channel:
        return None
    return sender, channel


def _redacted_irc_event(line: str) -> str:
    parts = _strip_tags_and_prefix(line).split(maxsplit=2)
    if not parts:
        return "unparsed"
    return " ".join(parts[:2])


def _private_message_target_and_text(parameters: str) -> tuple[str, str | None]:
    target_text, separator, trailing_text = parameters.partition(" :")
    if separator:
        target_parts = target_text.split()
        if target_parts:
            return target_parts[0], trailing_text
        return "", None

    parts = parameters.split(maxsplit=1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return "", None


def _nickname_from_prefix(prefix: str) -> str:
    return prefix.partition("!")[0]


def _response_target(private_message: IrcPrivateMessage, bot_name: str) -> str:
    if private_message.target.casefold() == bot_name.casefold():
        return private_message.sender
    return private_message.target


def _message_visibility(target: str) -> Literal["public", "private"]:
    if target.startswith(("#", "&", "+", "!")):
        return "public"
    return "private"


def _chat_text_from_irc_message(
    private_message: IrcPrivateMessage,
    bot_name: str,
    visibility: Literal["public", "private"],
) -> str | None:
    match visibility:
        case "private":
            return private_message.text
        case "public":
            return _public_chat_text(private_message.text, bot_name)


def _public_chat_text(text: str, bot_name: str) -> str | None:
    stripped_text = text.strip()
    folded_text = stripped_text.casefold()
    for command in ("!help", "!thank"):
        if folded_text == command or folded_text.startswith(f"{command} "):
            return _command_text(command, stripped_text)
    return _mentioned_chat_text(stripped_text, bot_name)


def _ctcp_version_response(text: str) -> str | None:
    if not text.startswith(f"{CTCP_DELIMITER}VERSION") or not text.endswith(CTCP_DELIMITER):
        return None
    version = text.removeprefix(f"{CTCP_DELIMITER}VERSION").removesuffix(
        CTCP_DELIMITER,
    )
    return version.strip() or None


def _current_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _command_text(command: str, text: str) -> str:
    command_name = command.removeprefix("!")
    command_remainder = text[len(command) :].strip()
    if command_remainder:
        return f"{command_name} {command_remainder}"
    return command_name


def _mentioned_chat_text(text: str, bot_name: str) -> str | None:
    if not text.casefold().startswith(bot_name.casefold()):
        return None
    remainder = text[len(bot_name) :]
    if remainder and remainder[0] not in {" ", ":", ","}:
        return None
    stripped_remainder = remainder.lstrip(" :,")
    if stripped_remainder:
        return stripped_remainder
    return "help"


def _write_line(writer: asyncio.StreamWriter, line: str) -> None:
    writer.write(f"{line}{IRC_LINE_ENDING}".encode())


async def _close_writer(writer: asyncio.StreamWriter) -> None:
    writer.close()
    try:
        await writer.wait_closed()
    except OSError as error:
        LOGGER.debug("ignored IRC writer close failure: %s", error)


async def _read_line(reader: asyncio.StreamReader) -> str:
    line = await reader.readline()
    if not line:
        return ""
    return line.decode("utf-8", errors="replace").rstrip("\r\n")


def _numeric_reply(line: str) -> str | None:
    parts = line.split()
    if len(parts) >= 2 and parts[1].isdigit() and len(parts[1]) == 3:
        return parts[1]
    return None


def _capability_tokens(line: str) -> set[str]:
    body = _strip_tags_and_prefix(line)
    _, separator, trailing = body.partition(" :")
    if separator:
        capability_text = trailing
    else:
        parts = body.split()
        if len(parts) < 4:
            return set()
        capability_start_index = 4 if parts[3] == CAPABILITY_CONTINUATION_MARKER else 3
        capability_text = " ".join(parts[capability_start_index:])
    return {token.partition("=")[0].casefold() for token in capability_text.split()}


def _is_capability_continuation(line: str) -> bool:
    parts = _strip_tags_and_prefix(line).split()
    return (
        len(parts) > 3
        and parts[0].casefold() == "cap"
        and parts[3] == CAPABILITY_CONTINUATION_MARKER
    )


def _cap_subcommand(line: str) -> str | None:
    parts = _strip_tags_and_prefix(line).split()
    if len(parts) >= 3 and parts[0].casefold() == "cap":
        return parts[2].casefold()
    return None


def _is_authenticate_continue(line: str) -> bool:
    parts = _strip_tags_and_prefix(line).split()
    return len(parts) >= 2 and parts[0].casefold() == "authenticate" and parts[1] == "+"


def _strip_tags_and_prefix(line: str) -> str:
    without_tags = line.partition(" ")[2] if line.startswith("@") else line
    return without_tags.partition(" ")[2] if without_tags.startswith(":") else without_tags
