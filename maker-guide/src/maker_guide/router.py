"""Event routing from socket ingestion into daemon logs."""

from __future__ import annotations

import asyncio
import logging
import re
import shlex
import sqlite3
from contextlib import suppress
from datetime import UTC
from pathlib import Path

from maker_guide.chat.presenter import format_tier_promotion_announcements
from maker_guide.curriculum.models import AllOfValidation, CommandHistoryValidation, CourseCatalog
from maker_guide.events import (
    IrcOutboundMessage,
    ShellEvent,
    format_shell_event_for_irc,
    redact_command,
)
from maker_guide.irc import enqueue_public_announcements
from maker_guide.progress.service import (
    complete_session_objective,
    current_session_objective,
    record_session_objective_validation_failure,
)
from maker_guide.progress.validation import (
    QuestValidationInput,
    validate_session_objective,
)
from maker_guide.repositories.audit_event import AuditEvent, append_audit_event
from maker_guide.repositories.cohort_membership import get_membership
from maker_guide.repositories.command_observation import CommandObservation, add_command_observation
from maker_guide.repositories.course_release import get_course_release
from maker_guide.repositories.helpers import connect_database, transaction

LOGGER = logging.getLogger(__name__)


async def route_events(
    ingest_queue: asyncio.Queue[ShellEvent],
    *,
    database_path: Path | None = None,
    catalog: CourseCatalog | None = None,
    outbound_queue: asyncio.Queue[IrcOutboundMessage] | None = None,
    irc_channels: tuple[str, ...] = (),
) -> None:
    """Log accepted shell events and persist selected validation evidence."""
    if (database_path is None) != (catalog is None):
        raise ValueError("database path and catalog must be provided together")

    while True:
        event = await ingest_queue.get()
        try:
            LOGGER.info("shell event: %s", format_shell_event_for_irc(event))
            if database_path is not None and catalog is not None:
                public_announcements = await _persist_selected_observation_in_worker(
                    database_path,
                    catalog,
                    event,
                )
                if outbound_queue is not None:
                    await enqueue_public_announcements(
                        outbound_queue,
                        irc_channels,
                        public_announcements,
                    )
        except sqlite3.Error as error:
            LOGGER.warning("could not persist shell observation: %s", error)
        finally:
            ingest_queue.task_done()


async def _persist_selected_observation_in_worker(
    database_path: Path,
    catalog: CourseCatalog,
    event: ShellEvent,
) -> tuple[str, ...]:
    if not _event_can_be_observed(event):
        return ()

    persistence_task = asyncio.create_task(
        asyncio.to_thread(_persist_selected_observation_from_path, database_path, catalog, event),
    )
    try:
        return await asyncio.shield(persistence_task)
    except asyncio.CancelledError:
        with suppress(sqlite3.Error):
            await persistence_task
        raise


def _persist_selected_observation_from_path(
    database_path: Path,
    catalog: CourseCatalog,
    event: ShellEvent,
) -> tuple[str, ...]:
    database_connection = connect_database(database_path)
    try:
        return _persist_selected_observation(database_connection, catalog, event)
    finally:
        database_connection.close()


def _persist_selected_observation(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    event: ShellEvent,
) -> tuple[str, ...]:
    if not _event_can_be_observed(event):
        return ()

    membership = get_membership(database_connection, event.username, catalog.course.id)
    course_release = get_course_release(database_connection, catalog.course.id)
    if membership is None or course_release is None:
        return ()

    with transaction(database_connection):
        public_announcements: tuple[str, ...] = ()
        if event.ssh_auth_method == "publickey" and not catalog.session_is_after(
            "S2", course_release.session_reached
        ):
            current_objective_result = current_session_objective(
                database_connection,
                catalog,
                handle=event.username,
            )
            if (
                current_objective_result.session_id == "S2"
                and current_objective_result.objective is not None
                and current_objective_result.objective.id == "ssh-public-key"
            ):
                audit_event_id = append_audit_event(
                    database_connection,
                    AuditEvent(
                        event_type="ssh_publickey_observed",
                        handle=event.username,
                        source="shell-hook",
                        created_at=_event_timestamp(event),
                        payload={"course_id": catalog.course.id},
                    ),
                )
                public_announcements = format_tier_promotion_announcements(
                    complete_session_objective(
                        database_connection,
                        catalog,
                        handle=event.username,
                        session_id="S2",
                        objective_id="ssh-public-key",
                        completed_at=_event_timestamp(event),
                        evidence={"audit_event_id": audit_event_id},
                        source="shell-hook",
                    ).tier_promotions,
                )
        try:
            shlex.split(event.command)
        except ValueError:
            return public_announcements
        command = " ".join(event.command.split())
        if not (
            _command_matches_observed_command(
                command,
                _available_observed_commands(catalog, course_release.session_reached),
            )
            or _command_matches_required_pattern(
                command,
                _available_required_patterns(catalog, course_release.session_reached),
            )
        ):
            return public_announcements
        if (
            add_command_observation(
                database_connection,
                CommandObservation(
                    id=None,
                    event_id=event.event_id,
                    handle=event.username,
                    course_id=catalog.course.id,
                    command=redact_command(command),
                    cwd=event.cwd,
                    phase=event.phase,
                    exit_status=event.exit_status,
                    observed_at=_event_timestamp(event),
                ),
            )
            is None
        ):
            return public_announcements
        return public_announcements + _complete_current_command_history_objective(
            database_connection,
            catalog,
            event,
            command,
        )


def _complete_current_command_history_objective(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    event: ShellEvent,
    command: str,
) -> tuple[str, ...]:
    objective_result = current_session_objective(
        database_connection,
        catalog,
        handle=event.username,
    )
    if objective_result.objective is None:
        return ()
    objective = objective_result.objective
    if not _command_matches_required_pattern(
        command,
        _validation_required_patterns(objective.validation),
    ):
        return ()
    validation_result = validate_session_objective(
        QuestValidationInput(
            database_connection=database_connection,
            catalog=catalog,
            handle=event.username,
            checked_at=_event_timestamp(event),
            assigned_at=objective_result.evidence_since,
        ),
        objective.validation,
    )
    if not validation_result.passed:
        record_session_objective_validation_failure(
            database_connection,
            catalog,
            handle=event.username,
            session_id=objective_result.session_id,
            objective_id=objective.id,
            failed_at=_event_timestamp(event),
            source="shell-hook",
            validation_result=validation_result,
        )
        return ()
    return format_tier_promotion_announcements(
        complete_session_objective(
            database_connection,
            catalog,
            handle=event.username,
            session_id=objective_result.session_id,
            objective_id=objective.id,
            completed_at=_event_timestamp(event),
            evidence=validation_result.evidence,
            source="shell-hook",
        ).tier_promotions,
    )


def _event_can_be_observed(event: ShellEvent) -> bool:
    return event.phase == "after" and event.exit_status == 0


def _available_observed_commands(catalog: CourseCatalog, session_reached: str) -> frozenset[str]:
    return frozenset(
        observed_command
        for quest in catalog.quests_available_through(session_reached)
        for observed_command in _validation_observed_commands(quest.validation)
    ) | frozenset(
        observed_command
        for session in catalog.sessions_through(session_reached)
        for objective in session.objectives
        for observed_command in _validation_observed_commands(objective.validation)
    )


def _available_required_patterns(catalog: CourseCatalog, session_reached: str) -> tuple[str, ...]:
    return tuple(
        required_pattern
        for quest in catalog.quests_available_through(session_reached)
        for required_pattern in _validation_required_patterns(quest.validation)
    ) + tuple(
        required_pattern
        for session in catalog.sessions_through(session_reached)
        for objective in session.objectives
        for required_pattern in _validation_required_patterns(objective.validation)
    )


def _validation_observed_commands(
    validation: CommandHistoryValidation | AllOfValidation | object,
) -> tuple[str, ...]:
    match validation:
        case CommandHistoryValidation(observed_commands=observed_commands):
            return observed_commands
        case AllOfValidation(validations=validations):
            return tuple(
                observed_command
                for child_validation in validations
                for observed_command in _validation_observed_commands(child_validation)
            )
        case _:
            return ()


def _validation_required_patterns(
    validation: CommandHistoryValidation | AllOfValidation | object,
) -> tuple[str, ...]:
    match validation:
        case CommandHistoryValidation(required_patterns=required_patterns):
            return required_patterns
        case AllOfValidation(validations=validations):
            return tuple(
                required_pattern
                for child_validation in validations
                for required_pattern in _validation_required_patterns(child_validation)
            )
        case _:
            return ()


def _command_matches_observed_command(command: str, observed_commands: frozenset[str]) -> bool:
    stripped_command = command.strip()
    return any(
        _matches_observed_command(stripped_command, observed_command)
        for observed_command in observed_commands
    )


def _matches_observed_command(command: str, observed_command: str) -> bool:
    stripped_observed_command = observed_command.strip()
    if not stripped_observed_command[0].isalpha():
        return stripped_observed_command in command
    return command == stripped_observed_command or command.startswith(
        f"{stripped_observed_command} ",
    )


def _command_matches_required_pattern(command: str, required_patterns: tuple[str, ...]) -> bool:
    return any(
        re.search(required_pattern, command) is not None for required_pattern in required_patterns
    )


def _event_timestamp(event: ShellEvent) -> str:
    return event.timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z")
