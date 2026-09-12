"""Tests for daemon-side CLI request routing."""

from __future__ import annotations

import asyncio
import sqlite3
import threading
from contextlib import closing
from pathlib import Path

import pytest

import maker_guide.cli.bot as bot_cli
from maker_guide.chat.contract import ChatDependencies, ChatRequest, ChatResponse, CliChatContext
from maker_guide.chat.snapshot import LearnerSnapshot
from maker_guide.config import AppConfig, DatabaseConfig, IrcConfig, SaslConfig, SocketConfig
from maker_guide.events import IrcOutboundMessage
from maker_guide.site_check import SITE_CHECK_CASES, SiteCheckError, SiteCheckReport
from maker_guide.unix_socket import SocketHelpRequest


@pytest.mark.parametrize(
    "site_check_mode", ["unsupported", "unused", "success", "error", "timeout"]
)
async def test_socket_help_broadcasts_public_announcements(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    site_check_mode: str,
) -> None:
    """The worker bridge is opt-in, bounded, transaction-free, and preserves announcements."""
    loop = asyncio.get_running_loop()
    loop_thread_id = threading.get_ident()
    calls: list[str] = []
    cancelled = asyncio.Event()
    report = SiteCheckReport(
        source_sha256="a" * 64,
        cases=tuple((case, True) for case in SITE_CHECK_CASES),
        error=None,
    )
    if site_check_mode == "timeout":
        monkeypatch.setattr(bot_cli, "SITE_CHECK_TIMEOUT_SECONDS", -2.8)

    async def run_site_check(source_sha256: str) -> SiteCheckReport:
        assert asyncio.get_running_loop() is loop
        assert threading.get_ident() == loop_thread_id
        calls.append(source_sha256)
        with closing(
            sqlite3.connect(temporary_path / "state.db", timeout=0)
        ) as database_connection:
            database_connection.execute("create table bridge_check (result text)")
        if site_check_mode == "error":
            raise SiteCheckError("invalid-report")
        if site_check_mode == "timeout":
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()
        return report

    def handle_chat_request(
        request: ChatRequest,
        dependencies: ChatDependencies,
    ) -> ChatResponse:
        assert request.context == CliChatContext(username="alice", terminal="/dev/pts/1")
        assert dependencies.bot_name == "guide"
        assert threading.get_ident() != loop_thread_id
        assert not dependencies.database_connection.in_transaction
        assert calls == []
        if site_check_mode == "unsupported":
            assert dependencies.site_check_runner is None
        else:
            assert dependencies.site_check_runner is not None
            if site_check_mode in {"error", "timeout"}:
                with pytest.raises(
                    SiteCheckError,
                    match="invalid-report" if site_check_mode == "error" else "timeout",
                ):
                    dependencies.site_check_runner("a" * 64)
            elif site_check_mode == "success":
                assert dependencies.site_check_runner("a" * 64) is report
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
                supports_site_check=site_check_mode != "unsupported",
                site_check_runner=(run_site_check if site_check_mode != "unsupported" else None),
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
    assert calls == ([] if site_check_mode in {"unsupported", "unused"} else ["a" * 64])
    if site_check_mode == "timeout":
        await asyncio.wait_for(cancelled.wait(), timeout=1)
