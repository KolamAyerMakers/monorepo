"""Tests for event routing."""

from __future__ import annotations

import asyncio
import logging
import sqlite3
import threading
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal, override

import maker_guide.router as router_module
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.curriculum.models import AllOfValidation, CourseCatalog, SessionObjectiveValidation
from maker_guide.events import IrcOutboundMessage, ShellEvent
from maker_guide.progress.service import (
    complete_session_objective,
    current_quest,
    current_session_objective,
)
from maker_guide.progress.validation import QuestValidationInput, QuestValidationResult
from maker_guide.repositories.audit_event import (
    list_recent_audit_events_by_type,
    list_unexported_audit_events,
)
from maker_guide.repositories.cohort_membership import CohortMembership, upsert_membership
from maker_guide.repositories.command_observation import list_recent_command_observations
from maker_guide.repositories.course_release import CourseRelease, upsert_course_release
from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.learner import Learner, upsert_learner
from maker_guide.repositories.quest_assignment import get_assignment
from maker_guide.repositories.quest_completion import get_quest_completion
from maker_guide.repositories.score_ledger import ScoreLedgerEntry, add_score_entry
from maker_guide.repositories.session_objective_completion import (
    SessionObjectiveCompletion,
    list_completed_objective_ids,
)
from maker_guide.repositories.session_objective_completion import (
    complete_session_objective as write_session_objective_completion,
)
from maker_guide.router import route_events

if TYPE_CHECKING:
    import pytest


class CapturingHandler(logging.Handler):
    """Logging handler that records emitted messages."""

    def __init__(self) -> None:
        super().__init__()
        self.messages: list[str] = []

    @override
    def emit(self, record: logging.LogRecord) -> None:
        """Capture a formatted log message."""
        self.messages.append(record.getMessage())


async def test_route_events_logs_shell_events_without_broadcasting() -> None:
    """Shell events are logged locally instead of emitted to IRC channels."""
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    capturing_handler = CapturingHandler()
    logger = logging.getLogger("maker_guide.router")
    previous_level = logger.level
    logger.setLevel(logging.INFO)
    logger.addHandler(capturing_handler)
    router_task = asyncio.create_task(route_events(ingest_queue))
    try:
        await ingest_queue.put(_shell_event(phase="before", command="git status"))
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)
        logger.removeHandler(capturing_handler)
        logger.setLevel(previous_level)

    assert capturing_handler.messages == ["shell event: alice before in /repo: git status"]


async def test_route_events_persists_selected_successful_observations(
    migrated_database_path: Path,
) -> None:
    """Successful postexec events for known learner quest commands become DB evidence."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        await ingest_queue.put(_shell_event(phase="after", command="whoami", exit_status=0))
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        assert [
            observation.command
            for observation in list_recent_command_observations(
                database_connection,
                "alice",
                CATALOG.course.id,
                observed_since="2026-07-19T08:00:00Z",
                limit=10,
            )
        ] == ["whoami"]


async def test_route_events_persists_public_key_evidence_and_completes_s2_objective(
    migrated_database_path: Path,
) -> None:
    """An unmatched public-key command atomically records and completes the SSH objective."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S2")
        _write_s1_objective_prerequisites(database_connection)
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        await ingest_queue.put(
            _shell_event(
                phase="after",
                command="printf connected",
                exit_status=0,
                ssh_auth_method="publickey",
            ),
        )
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        assert list_completed_objective_ids(
            database_connection,
            "alice",
            CATALOG.course.id,
            "S2",
        ) == frozenset({"ssh-public-key"})
        audit_events = list_recent_audit_events_by_type(
            database_connection,
            "ssh_publickey_observed",
            "alice",
            "2026-07-19T08:00:00Z",
            10,
        )
        assert len(audit_events) == 1
        assert database_connection.execute(
            """
            select evidence_json
            from session_objective_completions
            where session_id = 'S2' and objective_id = 'ssh-public-key'
            """,
        ).fetchone() == (f'{{"audit_event_id":{audit_events[0].id}}}',)


async def test_route_events_does_not_persist_public_key_evidence_before_s2_release(
    migrated_database_path: Path,
) -> None:
    """Public-key login has no persistence side effects before the S2 release."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S1")
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        await ingest_queue.put(
            _shell_event(
                phase="after",
                command="printf connected",
                exit_status=0,
                ssh_auth_method="publickey",
            ),
        )
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        assert database_connection.execute("select count(*) from audit_events").fetchone() == (0,)
        assert database_connection.execute(
            "select count(*) from session_objective_completions",
        ).fetchone() == (0,)
        assert database_connection.execute("select count(*) from score_ledger").fetchone() == (0,)
        assert database_connection.execute("select count(*) from tier_promotions").fetchone() == (
            0,
        )
        assert database_connection.execute("select count(*) from outbox_items").fetchone() == (0,)


async def test_route_events_does_not_complete_s2_ssh_objective_for_password_authentication(
    migrated_database_path: Path,
) -> None:
    """A successful password-authenticated command is not SSH key evidence."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S2")
        _write_s1_objective_prerequisites(database_connection)
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        await ingest_queue.put(
            _shell_event(
                phase="after",
                command="printf connected",
                exit_status=0,
                ssh_auth_method="password",
            ),
        )
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        assert (
            list_completed_objective_ids(
                database_connection,
                "alice",
                CATALOG.course.id,
                "S2",
            )
            == frozenset()
        )
        assert (
            list_recent_audit_events_by_type(
                database_connection,
                "ssh_publickey_observed",
                "alice",
                "2026-07-19T08:00:00Z",
                10,
            )
            == []
        )


async def test_route_events_rolls_back_public_key_evidence_when_completion_fails(
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed completion leaves neither proof nor score-related side effects."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S2")
        _write_s1_objective_prerequisites(database_connection)

    original_complete_session_objective = router_module.complete_session_objective

    def fail_after_completion(  # noqa: PLR0913
        database_connection: sqlite3.Connection,
        catalog: CourseCatalog,
        *,
        handle: str,
        session_id: str,
        objective_id: str,
        completed_at: str,
        evidence: dict[str, object],
        source: str = "system",
    ) -> object:
        original_complete_session_objective(
            database_connection,
            catalog,
            handle=handle,
            session_id=session_id,
            objective_id=objective_id,
            completed_at=completed_at,
            evidence=evidence,
            source=source,
        )
        raise sqlite3.IntegrityError("forced completion failure")

    monkeypatch.setattr(router_module, "complete_session_objective", fail_after_completion)
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        await ingest_queue.put(
            _shell_event(
                phase="after",
                command="printf connected",
                exit_status=0,
                ssh_auth_method="publickey",
            ),
        )
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        assert (
            list_completed_objective_ids(
                database_connection,
                "alice",
                CATALOG.course.id,
                "S2",
            )
            == frozenset()
        )
        assert (
            list_recent_audit_events_by_type(
                database_connection,
                "ssh_publickey_observed",
                "alice",
                "2026-07-19T08:00:00Z",
                10,
            )
            == []
        )
        assert database_connection.execute("select count(*) from score_ledger").fetchone() == (0,)
        assert database_connection.execute("select count(*) from outbox_items").fetchone() == (0,)


async def test_route_events_does_not_duplicate_public_key_completion(
    migrated_database_path: Path,
) -> None:
    """Later public-key commands do not append duplicate SSH objective proof."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S2")
        _write_s1_objective_prerequisites(database_connection)
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        for command in ("printf connected", "printf still-connected"):
            await ingest_queue.put(
                _shell_event(
                    phase="after",
                    command=command,
                    exit_status=0,
                    ssh_auth_method="publickey",
                ),
            )
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        assert (
            len(
                list_recent_audit_events_by_type(
                    database_connection,
                    "ssh_publickey_observed",
                    "alice",
                    "2026-07-19T08:00:00Z",
                    10,
                ),
            )
            == 1
        )
        assert database_connection.execute(
            """
            select count(*)
            from session_objective_completions
            where session_id = 'S2' and objective_id = 'ssh-public-key'
            """,
        ).fetchone() == (1,)
        assert database_connection.execute("select count(*) from score_ledger").fetchone() == (2,)
        assert database_connection.execute("select count(*) from tier_promotions").fetchone() == (
            0,
        )
        assert database_connection.execute("select count(*) from outbox_items").fetchone() == (1,)


async def test_route_events_completes_and_announces_command_history_objectives(
    migrated_database_path: Path,
) -> None:
    """Shell routing broadcasts a promotion from automatic objective completion."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, released_at="2026-07-18T08:30:00Z")
        _complete_irc_objective(database_connection)
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle="alice",
                course_id=CATALOG.course.id,
                amount=390,
                reason="test",
                related_type="test",
                related_id="before-shell-objective",
                created_at="2026-07-18T08:35:00Z",
            ),
        )
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    outbound_queue: asyncio.Queue[IrcOutboundMessage] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(
            ingest_queue,
            database_path=migrated_database_path,
            catalog=CATALOG,
            outbound_queue=outbound_queue,
            irc_channels=("#lf2607",),
        ),
    )
    try:
        for command in ("whoami", "date", "uptime"):
            await ingest_queue.put(
                _shell_event(
                    phase="after",
                    command=command,
                    exit_status=0,
                    timestamp=datetime(2026, 7, 18, 8, 45, tzinfo=UTC),
                ),
            )
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        objective_result = current_session_objective(
            database_connection,
            CATALOG,
            handle="alice",
        )
        assert objective_result.objective is not None
        assert objective_result.objective.id == "count-home-entries"
    assert outbound_queue.get_nowait() == IrcOutboundMessage(
        channel="#lf2607",
        text="alice became an apprentice",
    )


async def test_route_events_completes_composite_objectives_from_matching_commands(
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A matching command triggers deterministic validation of the current composite objective."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_objectives_before_build(database_connection)

    def validate_session_objective(
        validation_input: QuestValidationInput,
        validation: SessionObjectiveValidation,
    ) -> QuestValidationResult:
        assert validation_input.handle == "alice"
        assert isinstance(validation, AllOfValidation)
        return QuestValidationResult(passed=True, failure_reason=None, evidence={"passed": True})

    monkeypatch.setattr(router_module, "validate_session_objective", validate_session_objective)
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        await ingest_queue.put(_shell_event(phase="after", command="build-website", exit_status=0))
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        assert (
            current_session_objective(
                database_connection,
                CATALOG,
                handle="alice",
            ).objective
            is None
        )


async def test_route_events_audits_failed_objective_validation(
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Automatic objective checks retain operational failure evidence."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_objectives_before_build(database_connection)

    def validate_session_objective(
        validation_input: QuestValidationInput,
        validation: SessionObjectiveValidation,
    ) -> QuestValidationResult:
        assert validation_input.handle == "alice"
        assert isinstance(validation, AllOfValidation)
        return QuestValidationResult(
            passed=False,
            failure_reason="permission-denied",
            evidence={"validation_type": "path_exists", "passed": False},
        )

    monkeypatch.setattr(router_module, "validate_session_objective", validate_session_objective)
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        await ingest_queue.put(_shell_event(phase="after", command="build-website", exit_status=0))
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        audit_events = list_unexported_audit_events(database_connection, 20)
        assert next(
            event.payload
            for event in audit_events
            if event.event_type == "session_objective_validation_failed"
        ) == {
            "course_id": CATALOG.course.id,
            "evidence": {"passed": False, "validation_type": "path_exists"},
            "failure_reason": "permission-denied",
            "objective_id": "build-first-site",
            "session_id": "S1",
        }
        assert next(
            event.payload
            for event in audit_events
            if event.event_type == "operational_validation_failed"
        ) == {
            "course_id": CATALOG.course.id,
            "failure_reason": "permission-denied",
            "objective_id": "build-first-site",
            "session_id": "S1",
        }
        assert (
            current_session_objective(
                database_connection,
                CATALOG,
                handle="alice",
            ).objective
            == CATALOG.session("S1").objectives[-1]
        )


async def test_route_events_does_not_assign_s3_quest_before_objectives_complete(
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Completing only the first S3 objective leaves its quest unassigned."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(
            database_connection,
            session_reached="S3",
            released_at="2026-08-01T09:00:00Z",
        )
        _complete_session_objectives(database_connection, through_session_id="S2")

    def validate_session_objective(
        validation_input: QuestValidationInput,
        validation: SessionObjectiveValidation,
    ) -> QuestValidationResult:
        assert validation_input.assigned_at == "2026-08-01T09:00:00Z"
        assert isinstance(validation, AllOfValidation)
        return QuestValidationResult(passed=True, failure_reason=None, evidence={"passed": True})

    monkeypatch.setattr(router_module, "validate_session_objective", validate_session_objective)
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        await ingest_queue.put(
            _shell_event(
                phase="after",
                command="cat /etc/hostname >/dev/null",
                exit_status=0,
            ),
        )
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        assert list_completed_objective_ids(
            database_connection,
            "alice",
            CATALOG.course.id,
            "S3",
        ) == frozenset({"separate-standard-streams"})
        objective_result = current_session_objective(
            database_connection,
            CATALOG,
            handle="alice",
        )
        assert objective_result.objective is not None
        assert objective_result.objective.id == "make-first-pipe"
        assert (
            get_assignment(
                database_connection,
                "alice",
                CATALOG.course.id,
                "make-first-pipe",
            )
            is None
        )


async def test_route_events_does_not_complete_assigned_quest(
    migrated_database_path: Path,
) -> None:
    """Shell evidence cannot complete an assigned quest without an explicit check."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_session_objectives(database_connection)
        assert current_quest(
            database_connection,
            CATALOG,
            handle="alice",
            assigned_at="2026-07-19T08:59:00Z",
            source="test",
        ).quest == CATALOG.quest("prove-shell-alive")

    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        for command in ("whoami", "date", "uptime"):
            await ingest_queue.put(_shell_event(phase="after", command=command, exit_status=0))
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        assert (
            get_quest_completion(
                database_connection,
                "alice",
                CATALOG.course.id,
                "prove-shell-alive",
            )
            is None
        )
        assert database_connection.execute(
            "select count(*) from quest_attempts",
        ).fetchone() == (0,)


async def test_route_events_does_not_create_future_assignment_after_final_objective(
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An untrusted future hook timestamp cannot poison a quest assignment window."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_objectives_before_build(database_connection)

    def validate_session_objective(
        validation_input: QuestValidationInput,
        validation: SessionObjectiveValidation,
    ) -> QuestValidationResult:
        assert validation_input.handle == "alice"
        assert isinstance(validation, AllOfValidation)
        return QuestValidationResult(passed=True, failure_reason=None, evidence={"passed": True})

    monkeypatch.setattr(router_module, "validate_session_objective", validate_session_objective)
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        for command in ("whoami", "date", "uptime", "build-website"):
            await ingest_queue.put(
                _shell_event(
                    phase="after",
                    command=command,
                    exit_status=0,
                    timestamp=datetime(2999, 7, 19, 9, 0, tzinfo=UTC),
                ),
            )
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        assert (
            get_assignment(
                database_connection,
                "alice",
                CATALOG.course.id,
                "prove-shell-alive",
            )
            is None
        )
        assert (
            get_quest_completion(
                database_connection,
                "alice",
                CATALOG.course.id,
                "prove-shell-alive",
            )
            is None
        )
        assert database_connection.execute(
            "select count(*) from quest_attempts",
        ).fetchone() == (0,)


async def test_route_events_persists_commands_selected_by_required_pattern(
    migrated_database_path: Path,
) -> None:
    """Alias-expanded commands still become DB evidence for learner-facing commands."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        await ingest_queue.put(
            _shell_event(
                phase="after",
                command="maker-guide-build-personal-website",
                exit_status=0,
            ),
        )
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        assert [
            observation.command
            for observation in list_recent_command_observations(
                database_connection,
                "alice",
                CATALOG.course.id,
                observed_since="2026-07-19T08:00:00Z",
                limit=10,
            )
        ] == ["maker-guide-build-personal-website"]


async def test_route_events_redacts_selected_observation_secrets(
    migrated_database_path: Path,
) -> None:
    """Persisted command evidence redacts high-confidence secret fragments."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        await ingest_queue.put(
            _shell_event(
                phase="after",
                command=(
                    "whoami password=hunter2 token=abc secret=hidden "
                    "api_key=key123 api-key=key456 -H 'Authorization: Bearer deadbeef'"
                ),
                exit_status=0,
            ),
        )
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        persisted_commands = [
            observation.command
            for observation in list_recent_command_observations(
                database_connection,
                "alice",
                CATALOG.course.id,
                observed_since="2026-07-19T08:00:00Z",
                limit=10,
            )
        ]
    assert len(persisted_commands) == 1
    for redacted_fragment in (
        "password=[redacted]",
        "token=[redacted]",
        "secret=[redacted]",
        "api_key=[redacted]",
        "api-key=[redacted]",
        "Bearer [redacted]",
    ):
        assert redacted_fragment in persisted_commands[0]
    for raw_secret in ("hunter2", "abc", "hidden", "key123", "key456", "deadbeef"):
        assert raw_secret not in persisted_commands[0]


async def test_route_events_canonicalizes_selected_observation_whitespace(
    migrated_database_path: Path,
) -> None:
    """Persisted command evidence normalizes whitespace without adding quotes."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        await ingest_queue.put(
            _shell_event(
                phase="after",
                command="ls\t-la   ~",
                exit_status=0,
            ),
        )
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        assert [
            observation.command
            for observation in list_recent_command_observations(
                database_connection,
                "alice",
                CATALOG.course.id,
                observed_since="2026-07-19T08:00:00Z",
                limit=10,
            )
        ] == ["ls -la ~"]


async def test_route_events_skips_unselected_or_untrusted_observations(
    migrated_database_path: Path,
) -> None:
    """The router does not persist failed, before, unknown, or irrelevant shell events."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=migrated_database_path, catalog=CATALOG),
    )
    try:
        for event in (
            _shell_event(phase="before", command="whoami"),
            _shell_event(phase="after", command="date", exit_status=1),
            _shell_event(phase="after", command="rm -rf /tmp/example", exit_status=0),
            _shell_event(phase="after", command="whoami", exit_status=0, username="bob"),
        ):
            await ingest_queue.put(event)
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    with connect_database(migrated_database_path) as database_connection:
        assert (
            list_recent_command_observations(
                database_connection,
                "alice",
                CATALOG.course.id,
                observed_since="2026-07-19T08:00:00Z",
                limit=10,
            )
            == []
        )


async def test_route_events_opens_and_closes_database_in_worker_thread(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Router SQLite persistence does not use the event-loop thread."""
    event_loop_thread = threading.get_ident()
    opened_thread_id: int | None = None
    closed_thread_id: int | None = None

    class FakeConnection:
        def close(self) -> None:
            nonlocal closed_thread_id
            closed_thread_id = threading.get_ident()

    def connect_database(database_path: Path) -> FakeConnection:
        nonlocal opened_thread_id
        assert database_path == tmp_path / "state.db"
        opened_thread_id = threading.get_ident()
        return FakeConnection()

    def persist_selected_observation(
        database_connection: FakeConnection,
        catalog: object,
        event: ShellEvent,
    ) -> None:
        assert isinstance(database_connection, FakeConnection)
        assert catalog is CATALOG
        assert event.command == "whoami"

    monkeypatch.setattr(router_module, "connect_database", connect_database)
    monkeypatch.setattr(
        router_module,
        "_persist_selected_observation",
        persist_selected_observation,
    )

    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=tmp_path / "state.db", catalog=CATALOG),
    )
    try:
        await ingest_queue.put(_shell_event(phase="after", command="whoami", exit_status=0))
        await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    finally:
        await _cancel_router(router_task)

    assert opened_thread_id is not None
    assert closed_thread_id == opened_thread_id
    assert opened_thread_id != event_loop_thread


async def test_route_events_cancellation_waits_for_inflight_persistence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cancellation waits until the worker-thread persistence attempt has cleaned up."""
    worker_started = threading.Event()
    release_worker = threading.Event()
    worker_finished = threading.Event()

    def persist_selected_observation_from_path(
        database_path: Path,
        catalog: object,
        event: ShellEvent,
    ) -> None:
        assert database_path == tmp_path / "state.db"
        assert catalog is CATALOG
        assert event.command == "whoami"
        worker_started.set()
        release_worker.wait(timeout=5.0)
        worker_finished.set()

    monkeypatch.setattr(
        router_module,
        "_persist_selected_observation_from_path",
        persist_selected_observation_from_path,
    )

    ingest_queue: asyncio.Queue[ShellEvent] = asyncio.Queue()
    router_task = asyncio.create_task(
        route_events(ingest_queue, database_path=tmp_path / "state.db", catalog=CATALOG),
    )
    await ingest_queue.put(_shell_event(phase="after", command="whoami", exit_status=0))
    await asyncio.wait_for(asyncio.to_thread(worker_started.wait), timeout=1.0)

    router_task.cancel()
    await asyncio.sleep(0.05)
    assert not router_task.done()
    assert not worker_finished.is_set()

    release_worker.set()
    with suppress(asyncio.CancelledError):
        await asyncio.wait_for(router_task, timeout=1.0)
    await asyncio.wait_for(ingest_queue.join(), timeout=1.0)
    assert worker_finished.is_set()


def _shell_event(  # noqa: PLR0913
    *,
    phase: Literal["before", "after"],
    command: str,
    exit_status: int | None = None,
    event_id: str | None = None,
    username: str = "alice",
    ssh_auth_method: str | None = None,
    timestamp: datetime | None = None,
) -> ShellEvent:
    return ShellEvent(
        user_id=1001,
        username=username,
        process_id=1234,
        phase=phase,
        cwd="/repo",
        command=command,
        shell="bash",
        tty=None,
        exit_status=exit_status,
        execute=True,
        timestamp=timestamp or datetime(2026, 7, 19, 9, 0, tzinfo=UTC),
        ssh_auth_method=ssh_auth_method,
        event_id=event_id,
    )


async def _cancel_router(router_task: asyncio.Task[None]) -> None:
    router_task.cancel()
    with suppress(asyncio.CancelledError):
        await router_task


def _write_member(
    database_connection: sqlite3.Connection,
    session_reached: str = "S1",
    *,
    released_at: str = "2026-07-18T09:00:00Z",
) -> None:
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
    upsert_course_release(
        database_connection,
        CourseRelease(
            course_id=CATALOG.course.id,
            session_reached=session_reached,
            released_at=released_at,
        ),
    )


def _complete_irc_objective(database_connection: sqlite3.Connection) -> None:
    complete_session_objective(
        database_connection,
        CATALOG,
        handle="alice",
        session_id="S1",
        objective_id="join-course-irc",
        completed_at="2026-07-18T08:31:00Z",
        evidence={},
        source="test",
    )


def _write_s1_objective_prerequisites(database_connection: sqlite3.Connection) -> None:
    for objective in CATALOG.session("S1").objectives:
        write_session_objective_completion(
            database_connection,
            SessionObjectiveCompletion(
                handle="alice",
                course_id=CATALOG.course.id,
                session_id="S1",
                objective_id=objective.id,
                completed_at="2026-07-19T08:00:00Z",
                evidence_json="{}",
            ),
        )


def _complete_session_objectives(
    database_connection: sqlite3.Connection,
    through_session_id: str = "S1",
) -> None:
    for session in CATALOG.sessions_through(through_session_id):
        for objective in session.objectives:
            write_session_objective_completion(
                database_connection,
                SessionObjectiveCompletion(
                    handle="alice",
                    course_id=CATALOG.course.id,
                    session_id=session.id,
                    objective_id=objective.id,
                    completed_at="2026-07-19T08:00:00Z",
                    evidence_json="{}",
                ),
            )


def _complete_objectives_before_build(database_connection: sqlite3.Connection) -> None:
    for objective_id in (
        "join-course-irc",
        "prove-shell-alive",
        "count-home-entries",
        "read-man-ls",
    ):
        complete_session_objective(
            database_connection,
            CATALOG,
            handle="alice",
            session_id="S1",
            objective_id=objective_id,
            completed_at="2026-07-19T08:00:00Z",
            evidence={},
            source="test",
        )
