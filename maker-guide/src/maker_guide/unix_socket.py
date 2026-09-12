"""Unix domain socket ingestion for shell preexec events."""

from __future__ import annotations

import asyncio
import grp
import json
import logging
import os
import pwd
import re
import socket
import stat
import struct
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol, Self, cast, runtime_checkable

from maker_guide.config import SocketConfig
from maker_guide.events import EventParseError, PeerCredentials, ShellEvent, parse_shell_event
from maker_guide.site_check import (
    SITE_CHECK_TIMEOUT_SECONDS,
    SITE_CHECK_VERSION,
    SiteCheckError,
    SiteCheckReport,
    parse_site_check_report,
)

LOGGER = logging.getLogger(__name__)
LINUX_PEER_CREDENTIAL_FORMAT = "3i"
_SITE_CHECK_MAX_FRAME_BYTES = 4096
type HelpChunkWriter = Callable[[str], None]
type HelpRequestHandler = Callable[["SocketHelpRequest", HelpChunkWriter | None], Awaitable[str]]


@dataclass(frozen=True, kw_only=True, slots=True)
class SocketHelpRequest:
    """One CLI help request submitted through the daemon socket."""

    username: str
    terminal: str | None
    text: str
    cwd: str | None = None
    ssh_connection: str | None = None
    stream: bool = False
    supports_site_check: bool = False
    site_check_runner: Callable[[str], Awaitable[SiteCheckReport]] | None = None
    """Server-only, one-shot continuation on this authenticated connection."""


@runtime_checkable
class PeerSocket(Protocol):
    """Socket-like object exposing Linux peer credential lookup."""

    def getsockopt(self, level: int, option: int, size: int) -> bytes:
        """Return a socket option as bytes."""
        ...


@dataclass(frozen=True, kw_only=True, slots=True)
class PeerAuthorizer:
    """Authorizes peer credentials for a multi-user daemon socket."""

    allowed_user_ids: frozenset[int]
    allowed_group: str | None

    @classmethod
    def from_config(cls, config: SocketConfig) -> Self:
        """Create an authorizer from socket configuration."""
        return cls(allowed_user_ids=config.allowed_user_ids, allowed_group=config.allowed_group)

    def is_allowed(self, credentials: PeerCredentials) -> bool:
        """Return whether the peer is permitted to submit events."""
        if credentials.user_id in self.allowed_user_ids:
            return True
        if self.allowed_group is None:
            return not self.allowed_user_ids
        try:
            group_entry = grp.getgrnam(self.allowed_group)
            user_entry = pwd.getpwuid(credentials.user_id)
        except KeyError:
            return False
        return (
            user_entry.pw_name in group_entry.gr_mem or credentials.group_id == group_entry.gr_gid
        )

    def username_for(self, credentials: PeerCredentials) -> str:
        """Resolve a peer UID to a username, falling back to the numeric UID."""
        try:
            return pwd.getpwuid(credentials.user_id).pw_name
        except KeyError:
            return str(credentials.user_id)


class UnixSocketServer:
    """Async Unix socket server for preexec events."""

    def __init__(
        self,
        config: SocketConfig,
        ingest_queue: asyncio.Queue[ShellEvent],
        authorizer: PeerAuthorizer | None = None,
        help_handler: HelpRequestHandler | None = None,
    ) -> None:
        self._config = config
        self._ingest_queue = ingest_queue
        self._authorizer = authorizer or PeerAuthorizer.from_config(config)
        self._help_handler = help_handler
        self._server: asyncio.Server | None = None

    async def start(self) -> None:
        """Bind and start listening on the configured socket path."""
        _prepare_socket_path(self._config.path)
        old_umask = os.umask(0o117)
        try:
            self._server = await asyncio.start_unix_server(
                self._handle_client,
                path=str(self._config.path),
                backlog=self._config.backlog,
                limit=self._config.max_line_bytes + 1,
            )
        finally:
            os.umask(old_umask)
        self._config.path.chmod(self._config.mode)

    async def close(self) -> None:
        """Stop the server and remove the socket path."""
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        if self._config.path.exists() and stat.S_ISSOCK(self._config.path.stat().st_mode):
            self._config.path.unlink()

    async def serve_forever(self) -> None:
        """Run until cancelled."""
        if self._server is None:
            await self.start()
        if self._server is None:
            raise RuntimeError("server did not start")
        async with self._server:
            await self._server.serve_forever()

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            credentials = _peer_credentials(writer)
            if not self._authorizer.is_allowed(credentials):
                await _write_response(writer, False, "unauthorized")
                return

            try:
                payload = await asyncio.wait_for(
                    reader.readline(),
                    timeout=self._config.read_timeout_seconds,
                )
            except ValueError:
                await _write_response(writer, False, "payload too large")
                return
            if not payload:
                await _write_response(writer, False, "empty payload")
                return
            if len(payload) > self._config.max_line_bytes:
                await _write_response(writer, False, "payload too large")
                return

            await self._handle_payload(payload.rstrip(b"\n"), credentials, reader, writer)
        except TimeoutError:
            await _write_response(writer, False, "timed out")
        except (EventParseError, OSError) as error:
            LOGGER.warning("rejected socket event: %s", error)
            await _write_response(writer, False, str(error))
        finally:
            await _close_writer(writer)

    async def _handle_payload(
        self,
        payload: bytes,
        credentials: PeerCredentials,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        if _is_help_request(payload):
            await self._handle_help_request(payload, credentials, reader, writer)
            return

        response_requested = _response_requested(payload)
        event = parse_shell_event(
            payload,
            credentials,
            self._authorizer.username_for(credentials),
        )
        try:
            self._ingest_queue.put_nowait(event)
        except asyncio.QueueFull:
            LOGGER.warning(
                "dropped socket event because ingest queue is full: user=%s phase=%s command=%r",
                event.username,
                event.phase,
                event.command,
            )
            if response_requested:
                await _write_response(writer, False, "queue full")
            return
        if response_requested:
            await _write_response(writer, True, None)

    async def _handle_help_request(  # noqa: C901 - Keep continuation state with its connection.
        self,
        payload: bytes,
        credentials: PeerCredentials,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        if self._help_handler is None:
            await _write_response(writer, False, "help handler is not configured")
            return
        site_check_used = False
        request_active = True

        async def run_site_check(source_sha256: str) -> SiteCheckReport:
            nonlocal site_check_used
            if site_check_used or not request_active:
                raise SiteCheckError("invalid-report")
            site_check_used = True
            if re.fullmatch("[0-9a-f]{64}", source_sha256) is None:
                raise SiteCheckError("invalid-report")
            try:
                if _peer_credentials(writer) != credentials:
                    raise SiteCheckError("invalid-report")
                async with asyncio.timeout(SITE_CHECK_TIMEOUT_SECONDS + 2.0):
                    writer.write(
                        json.dumps(
                            {
                                "ok": True,
                                "site_check": {
                                    "version": SITE_CHECK_VERSION,
                                    "source_sha256": source_sha256,
                                },
                            },
                            separators=(",", ":"),
                        ).encode("utf-8")
                        + b"\n",
                    )
                    await writer.drain()
                    result = await reader.readline()
                if not result.endswith(b"\n") or len(result) > min(
                    self._config.max_line_bytes, _SITE_CHECK_MAX_FRAME_BYTES
                ):
                    raise SiteCheckError("invalid-report")
                loaded = cast(
                    "object",
                    json.loads(result.decode("utf-8"), object_pairs_hook=_unique_json_fields),
                )
                if not isinstance(loaded, dict):
                    raise SiteCheckError("invalid-report")
                result_object = cast("dict[object, object]", loaded)
                if (
                    set(result_object) != {"kind", "report"}
                    or result_object["kind"] != "site_check_result"
                ):
                    raise SiteCheckError("invalid-report")
                return parse_site_check_report(result_object["report"], source_sha256)
            except (ValueError, OSError, RecursionError):
                raise SiteCheckError("invalid-report") from None

        try:
            await self._ingest_queue.join()
            help_request = _parse_help_request(payload, self._authorizer.username_for(credentials))
            if help_request.supports_site_check:
                help_request = replace(help_request, site_check_runner=run_site_check)
            chunk_writer = _help_chunk_writer(writer) if help_request.stream else None
            response_text = await self._help_handler(help_request, chunk_writer)
        except SiteCheckError:
            await _write_response(writer, False, "site check failed")
            return
        except EventParseError as error:
            await _write_response(writer, False, str(error))
            return
        except RuntimeError as error:
            await _write_response(writer, False, str(error))
            return
        finally:
            request_active = False
        await _write_response(writer, True, None, text=response_text)


def _help_chunk_writer(writer: asyncio.StreamWriter) -> HelpChunkWriter:
    loop = asyncio.get_running_loop()

    def write_chunk(chunk: str) -> None:
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None
        if current_loop is loop:
            _write_chunk_now(writer, chunk)
            return
        asyncio.run_coroutine_threadsafe(_write_chunk(writer, chunk), loop).result()

    return write_chunk


def _prepare_socket_path(path: Path) -> None:
    path.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
    _apply_setgid(path.parent)
    if not path.exists():
        return
    if stat.S_ISSOCK(path.stat().st_mode):
        path.unlink()
        return
    raise RuntimeError(f"refusing to replace non-socket path: {path}")


def _apply_setgid(path: Path) -> None:
    mode = path.stat().st_mode
    if not mode & stat.S_ISGID:
        path.chmod(mode | stat.S_ISGID)


def _peer_credentials(writer: asyncio.StreamWriter) -> PeerCredentials:
    socket_object = cast("object", writer.get_extra_info("socket"))
    if not isinstance(socket_object, PeerSocket):
        raise OSError("missing peer socket")
    credential_bytes = socket_object.getsockopt(
        socket.SOL_SOCKET,
        socket.SO_PEERCRED,
        struct.calcsize(LINUX_PEER_CREDENTIAL_FORMAT),
    )
    process_id, user_id, group_id = cast(
        "tuple[int, int, int]",
        struct.unpack(LINUX_PEER_CREDENTIAL_FORMAT, credential_bytes),
    )
    return PeerCredentials(process_id=process_id, user_id=user_id, group_id=group_id)


async def _write_response(
    writer: asyncio.StreamWriter,
    ok: bool,
    error: str | None,
    *,
    execute: bool = True,
    text: str | None = None,
) -> None:
    response: dict[str, object] = {"ok": ok, "execute": execute}
    if error is not None:
        response["error"] = error
    if text is not None:
        response["text"] = text
    try:
        writer.write(json.dumps(response, separators=(",", ":")).encode("utf-8") + b"\n")
        await writer.drain()
    except ConnectionError:
        return


async def _write_chunk(writer: asyncio.StreamWriter, chunk: str) -> None:
    try:
        _write_chunk_now(writer, chunk)
        await writer.drain()
    except ConnectionError:
        return


def _write_chunk_now(writer: asyncio.StreamWriter, chunk: str) -> None:
    writer.write(
        json.dumps(
            {"ok": True, "chunk": chunk},
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n",
    )


async def _close_writer(writer: asyncio.StreamWriter) -> None:
    writer.close()
    try:
        await writer.wait_closed()
    except ConnectionError:
        return


def _response_requested(payload: bytes) -> bool:
    try:
        loaded = cast("object", json.loads(payload.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return True
    if not isinstance(loaded, dict):
        return True
    return cast("dict[object, object]", loaded).get("reply") is not False


def _is_help_request(payload: bytes) -> bool:
    try:
        loaded = cast(
            "object",
            json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_json_fields),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise EventParseError("payload must be valid UTF-8 JSON") from error
    if not isinstance(loaded, dict):
        return False
    request_object = cast("dict[object, object]", loaded)
    if "kind" in request_object and request_object["kind"] != "help":
        raise EventParseError("unsupported request kind")
    return request_object.get("kind") == "help"


def _unique_json_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    fields = dict(pairs)
    if len(fields) != len(pairs):
        raise EventParseError("duplicate JSON fields")
    return fields


def _parse_help_request(  # noqa: C901 - Validate the small, fixed request directly.
    payload: bytes,
    username: str,
) -> SocketHelpRequest:
    try:
        loaded = cast(
            "object",
            json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_json_fields),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise EventParseError("payload must be valid UTF-8 JSON") from error
    if not isinstance(loaded, dict):
        raise EventParseError("payload must be a JSON object")
    request_object = cast("dict[object, object]", loaded)
    if request_object.keys() - {
        "version",
        "kind",
        "text",
        "terminal",
        "cwd",
        "ssh_connection",
        "stream",
        "supports_site_check",
    }:
        raise EventParseError("unknown help request fields")
    if type(request_object.get("version")) is not int or request_object["version"] != 1:
        raise EventParseError("version must be 1")
    if request_object.get("kind") != "help":
        raise EventParseError("kind must be help")
    text = request_object.get("text")
    if not isinstance(text, str):
        raise EventParseError("text must be a string")
    terminal = request_object.get("terminal")
    if terminal is not None and not isinstance(terminal, str):
        raise EventParseError("terminal must be null or a string")
    cwd = request_object.get("cwd")
    if cwd is not None and not isinstance(cwd, str):
        raise EventParseError("cwd must be null or a string")
    ssh_connection = request_object.get("ssh_connection")
    if ssh_connection is not None and not isinstance(ssh_connection, str):
        raise EventParseError("ssh_connection must be null or a string")
    for field in ("stream", "supports_site_check"):
        if not isinstance(request_object.get(field, False), bool):
            raise EventParseError("help capabilities must be booleans")
    return SocketHelpRequest(
        username=username,
        terminal=terminal,
        text=text,
        cwd=cwd,
        ssh_connection=ssh_connection,
        stream=request_object.get("stream") is True,
        supports_site_check=request_object.get("supports_site_check") is True,
    )
