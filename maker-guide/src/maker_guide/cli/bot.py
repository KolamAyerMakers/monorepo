"""Daemon entrypoint."""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Annotated

import typer
from rich.logging import RichHandler

from maker_guide.chat.contract import ChatDependencies, ChatRequest, ChatResponse, CliChatContext
from maker_guide.chat.service import handle_chat_request
from maker_guide.config import DEFAULT_CONFIG_PATH, AppConfig, LlmTutorConfig, load_config
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG
from maker_guide.events import IrcOutboundMessage, ShellEvent
from maker_guide.irc import IrcClient, IrcClientOptions, enqueue_public_announcements
from maker_guide.llm_tutor import (
    DEFAULT_TUTOR_MAX_TOKENS,
    TutorProviderClient,
    TutorProviderSettings,
    tutor_client_from_settings,
)
from maker_guide.repositories.helpers import connect_database
from maker_guide.router import route_events
from maker_guide.unix_socket import HelpChunkWriter, SocketHelpRequest, UnixSocketServer

app = typer.Typer(
    add_completion=False,
    help="Run the Kolam Makers bot daemon.",
    pretty_exceptions_enable=False,
)


def main() -> None:
    """Run the bot daemon from command-line arguments."""
    app()


@app.command()
def daemon(
    configuration_path: Annotated[
        Path,
        typer.Option("--config", help="Path to the daemon TOML configuration."),
    ] = DEFAULT_CONFIG_PATH,
) -> None:
    """Run the bot daemon."""
    configuration = load_config(configuration_path)
    logging.basicConfig(
        level=configuration.log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    asyncio.run(_run_daemon(configuration))


async def _run_daemon(configuration: AppConfig) -> None:
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue(
        maxsize=configuration.socket.queue_size,
    )
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue(
        maxsize=configuration.irc.outbound_queue_size,
    )
    tutor_client = _tutor_client_from_config(configuration.llm_tutor)
    unix_socket_server = UnixSocketServer(
        configuration.socket,
        ingest_queue,
        help_handler=lambda request, chunk_writer: _handle_socket_help_request(
            request,
            configuration,
            tutor_client,
            chunk_writer,
            outbound_queue,
        ),
    )
    await unix_socket_server.start()
    try:
        async with asyncio.TaskGroup() as task_group:
            task_group.create_task(unix_socket_server.serve_forever())
            task_group.create_task(
                route_events(
                    ingest_queue,
                    database_path=configuration.database.path,
                    catalog=DEFAULT_CATALOG,
                    outbound_queue=outbound_queue,
                    irc_channels=configuration.irc.channels,
                ),
            )
            task_group.create_task(
                IrcClient(
                    configuration.irc,
                    outbound_queue,
                    options=IrcClientOptions(
                        database_path=configuration.database.path,
                        catalog=DEFAULT_CATALOG,
                        tutor_client=tutor_client,
                        answer_interpreter=tutor_client,
                        tutor_max_tokens=(
                            DEFAULT_TUTOR_MAX_TOKENS
                            if configuration.llm_tutor is None
                            else configuration.llm_tutor.max_tokens
                        ),
                    ),
                ).run_forever(),
            )
    finally:
        await unix_socket_server.close()


def _tutor_client_from_config(configuration: LlmTutorConfig | None) -> TutorProviderClient | None:
    if configuration is None:
        return None
    return tutor_client_from_settings(
        TutorProviderSettings(
            provider=configuration.provider,
            model=configuration.model,
            api_key=configuration.api_key,
            timeout_seconds=configuration.timeout_seconds,
            max_tokens=configuration.max_tokens,
            rate_limit_per_minute=configuration.rate_limit_per_minute,
        ),
    )


async def _handle_socket_help_request(
    request: SocketHelpRequest,
    configuration: AppConfig,
    tutor_client: TutorProviderClient | None,
    chunk_writer: HelpChunkWriter | None,
    outbound_queue: asyncio.Queue[IrcOutboundMessage],
) -> str:
    def handle_request() -> ChatResponse:
        with connect_database(configuration.database.path) as database_connection:
            try:
                return handle_chat_request(
                    ChatRequest(
                        context=CliChatContext(
                            username=request.username,
                            terminal=request.terminal,
                            ssh_connection=request.ssh_connection,
                        ),
                        visibility="private",
                        text=request.text,
                    ),
                    ChatDependencies(
                        database_connection=database_connection,
                        catalog=DEFAULT_CATALOG,
                        bot_name=configuration.irc.nickname,
                        tutor_client=tutor_client,
                        answer_interpreter=tutor_client,
                        tutor_max_tokens=(
                            DEFAULT_TUTOR_MAX_TOKENS
                            if configuration.llm_tutor is None
                            else configuration.llm_tutor.max_tokens
                        ),
                        response_chunk_writer=chunk_writer,
                    ),
                )
            except sqlite3.Error as error:
                raise RuntimeError(str(error)) from error

    response = await asyncio.to_thread(handle_request)
    await enqueue_public_announcements(
        outbound_queue,
        configuration.irc.channels,
        response.public_announcements,
    )
    return response.text
