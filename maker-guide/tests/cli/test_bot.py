"""Tests for daemon-side CLI request routing."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import maker_guide.cli.bot as bot_cli
from maker_guide.chat.contract import ChatDependencies, ChatRequest, ChatResponse, CliChatContext
from maker_guide.chat.snapshot import LearnerSnapshot
from maker_guide.config import AppConfig, DatabaseConfig, IrcConfig, SaslConfig, SocketConfig
from maker_guide.events import IrcOutboundMessage
from maker_guide.unix_socket import SocketHelpRequest

if TYPE_CHECKING:
    import pytest


async def test_socket_help_broadcasts_public_announcements(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The daemon preserves public announcements from private CLI responses."""

    def handle_chat_request(
        request: ChatRequest,
        dependencies: ChatDependencies,
    ) -> ChatResponse:
        assert request.context == CliChatContext(username="alice", terminal="/dev/pts/1")
        assert dependencies.bot_name == "guide"
        return ChatResponse(
            text="next objective",
            learner_snapshot=LearnerSnapshot(
                handle="alice",
                course_id="lf2607",
                current_session="S1",
                taught_commands=(),
                taught_skills=(),
                pending_quests=(),
                completed_quests=(),
                score=500,
                tier="apprentice",
                recent_help_topics=(),
            ),
            public_announcements=("alice became an apprentice",),
        )

    monkeypatch.setattr(bot_cli, "handle_chat_request", handle_chat_request)
    configuration = AppConfig(
        socket=SocketConfig(path=temporary_path / "maker-guide.sock"),
        database=DatabaseConfig(path=temporary_path / "state.db"),
        irc=IrcConfig(
            server="irc.example",
            port=6697,
            nickname="guide",
            username="guide",
            realname="Guide",
            channels=("#lf2607", "#staff"),
            sasl=SaslConfig(username="guide", password="secret"),
        ),
    )
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()

    assert (
        await bot_cli._handle_socket_help_request(  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
            SocketHelpRequest(
                username="alice",
                terminal="/dev/pts/1",
                text="check",
            ),
            configuration,
            None,
            None,
            outbound_queue,
        )
        == "next objective"
    )
    assert (outbound_queue.get_nowait(), outbound_queue.get_nowait()) == (
        IrcOutboundMessage(channel="#lf2607", text="alice became an apprentice"),
        IrcOutboundMessage(channel="#staff", text="alice became an apprentice"),
    )
