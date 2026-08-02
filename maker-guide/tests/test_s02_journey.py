"""End-to-end S2 learner journey coverage."""

# ruff: noqa: PLR0915

from __future__ import annotations

import asyncio
import sqlite3
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

from maker_guide.chat.contract import ChatDependencies, ChatRequest, CliChatContext
from maker_guide.chat.service import handle_chat_request
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.events import ShellEvent
from maker_guide.progress.models import CourseReleaseInput
from maker_guide.progress.service import complete_session_objective, release_course
from maker_guide.repositories.audit_event import list_recent_audit_events_by_type
from maker_guide.repositories.cohort_membership import CohortMembership, upsert_membership
from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.learner import Learner, upsert_learner
from maker_guide.repositories.quest_completion import QuestCompletion, complete_quest
from maker_guide.repositories.session_objective_completion import list_completed_objective_ids
from maker_guide.router import route_events
from maker_guide.validation_paths import UnixAccount


async def test_s2_learner_journey(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """S2 work takes priority, records SSH proof, then returns to incomplete S1 work."""
    learner_home = temporary_path / "alice"
    learner_home.mkdir()

    def account_lookup(handle: str) -> UnixAccount | None:
        if handle != "alice":
            return None
        return UnixAccount(
            handle="alice",
            user_id=learner_home.stat().st_uid,
            home_directory=learner_home,
        )

    def guide(database_connection: sqlite3.Connection, text: str, timestamp: str) -> str:
        return handle_chat_request(
            ChatRequest(
                context=CliChatContext(username="alice", terminal="/dev/pts/1"),
                visibility="private",
                text=text,
            ),
            ChatDependencies(
                database_connection=database_connection,
                catalog=CATALOG,
                bot_name="guide-test",
                timestamp_factory=lambda: timestamp,
                account_lookup=account_lookup,
            ),
        ).text

    async def route_successful_commands(commands: tuple[str, ...], timestamp: datetime) -> None:
        ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
        router_task = asyncio.create_task(
            route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
        )
        try:
            for command in commands:
                await ingest_queue.put(
                    ShellEvent(
                        phase="after",
                        user_id=learner_home.stat().st_uid,
                        username="alice",
                        process_id=1,
                        cwd=str(learner_home),
                        command=command,
                        shell="bash",
                        tty="/dev/pts/1",
                        exit_status=0,
                        execute=True,
                        timestamp=timestamp,
                    ),
                )
            await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
        finally:
            router_task.cancel()
            with suppress(asyncio.CancelledError):
                await router_task

    with connect_database(migrated_database_path) as database_connection:
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
                course_id=CATALOG.course.id,
                joined_at="2026-07-18T09:00:00Z",
            ),
        )
        release_course(
            database_connection,
            CATALOG,
            CourseReleaseInput(
                session_reached="S1",
                updated_at="2026-07-18T09:00:00Z",
                source="test",
            ),
        )
        for objective in CATALOG.session("S1").objectives:
            complete_session_objective(
                database_connection,
                CATALOG,
                handle="alice",
                session_id="S1",
                objective_id=objective.id,
                completed_at="2026-07-18T09:00:00Z",
                evidence={},
                source="test",
            )

        assert "Today's quest: Prove the shell is alive" in guide(
            database_connection,
            "now",
            "2026-07-24T09:00:00Z",
        )

        release_course(
            database_connection,
            CATALOG,
            CourseReleaseInput(
                session_reached="S2",
                updated_at="2026-07-25T09:00:00Z",
                source="test",
            ),
        )
        assert "Current session objective: Connect with an SSH public key" in guide(
            database_connection,
            "now",
            "2026-07-25T09:01:00Z",
        )

    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        await ingest_queue.put(
            ShellEvent(
                phase="after",
                user_id=learner_home.stat().st_uid,
                username="alice",
                process_id=1,
                cwd=str(learner_home),
                command="printf connected",
                shell="bash",
                tty="/dev/pts/1",
                exit_status=0,
                execute=True,
                timestamp=datetime(2026, 7, 25, 9, 2, tzinfo=UTC),
                ssh_auth_method="publickey",
            ),
        )
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        router_task.cancel()
        with suppress(asyncio.CancelledError):
            await router_task

    with connect_database(migrated_database_path) as database_connection:
        audit_events = list_recent_audit_events_by_type(
            database_connection,
            "ssh_publickey_observed",
            "alice",
            "2026-07-25T09:00:00Z",
            1,
        )
        assert len(audit_events) == 1
        assert list_completed_objective_ids(
            database_connection,
            "alice",
            CATALOG.course.id,
            "S2",
        ) == frozenset({"ssh-public-key"})
        assert "Today's quest: Build a playground" in guide(
            database_connection,
            "now",
            "2026-07-25T09:03:00Z",
        )

        for quest_id in (
            "build-playground",
            "edit-with-micro",
            "redirect-and-append",
            "copy-and-inspect-ownership",
        ):
            complete_quest(
                database_connection,
                QuestCompletion(
                    handle="alice",
                    course_id=CATALOG.course.id,
                    quest_id=quest_id,
                    attempt_id=None,
                    completed_at="2026-07-25T09:04:00Z",
                    source="test",
                ),
            )
        database_connection.commit()

        assert "Today's quest: Personalize your homepage" in guide(
            database_connection,
            "now",
            "2026-07-25T09:13:00Z",
        )
        source_path = learner_home / "src" / "pages" / "index.md"
        source_path.parent.mkdir(parents=True)
        source_path.write_text("# Alice's page\n", encoding="utf-8")
        output_path = learner_home / "public_html" / "index.html"
        output_path.parent.mkdir()
        output_path.write_text("<h1>Alice's page</h1>\n", encoding="utf-8")
        await route_successful_commands(
            ("maker-guide-build-personal-website",),
            datetime(2026, 7, 25, 9, 14, tzinfo=UTC),
        )
        assert "Completed quest: Personalize your homepage" in guide(
            database_connection,
            "check",
            "2026-07-25T09:15:00Z",
        )
        assert "Today's quest: Prove the shell is alive" in guide(
            database_connection,
            "now",
            "2026-07-25T09:16:00Z",
        )
