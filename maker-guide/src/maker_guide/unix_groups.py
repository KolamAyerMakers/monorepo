"""Unix group reconciliation from SQLite intent."""

from __future__ import annotations

import grp
import pwd
import sqlite3
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from maker_guide.repositories.audit_event import AuditEvent, append_audit_event
from maker_guide.repositories.group_grant import (
    GroupGrant,
    GroupIntendedState,
    list_all_group_grants,
)
from maker_guide.repositories.helpers import RepositoryError
from maker_guide.repositories.outbox_item import (
    GROUP_SYNC_OUTBOX_KIND,
    OutboxItem,
    list_retryable_outbox_item_ids_by_kind,
    list_retryable_outbox_items_by_kind,
    mark_outbox_item_failed,
    mark_outbox_item_processed,
    validate_group_sync_outbox_item,
)
from maker_guide.unix_names import is_safe_unix_name

UNIX_GROUP_COMMAND_TIMEOUT_SECONDS = 10.0


class UnixGroupSyncError(RuntimeError):
    """Raised when Unix group reconciliation cannot complete."""


@dataclass(frozen=True, kw_only=True, slots=True)
class UnixGroupCommand:
    """One command invocation."""

    arguments: tuple[str, ...]
    """Complete command arguments, including executable name."""


@dataclass(frozen=True, kw_only=True, slots=True)
class UnixGroupCommandResult:
    """Result returned by a command runner."""

    return_code: int
    """Process return code."""
    stdout: str
    """Captured standard output."""
    stderr: str
    """Captured standard error."""


@dataclass(frozen=True, kw_only=True, slots=True)
class UnixGroupChange:
    """One planned Unix group membership change."""

    handle: str
    """Learner handle to mutate."""
    group_name: str
    """Unix group to mutate."""
    intended_state: GroupIntendedState
    """Desired membership state after applying the change."""
    reason: str
    """Reason from SQLite group intent."""


@dataclass(frozen=True, kw_only=True, slots=True)
class UnixGroupSyncOptions:
    """Options for one Unix group reconciliation."""

    dry_run: bool
    """Whether to plan changes without applying helper mutations."""
    synced_at: str
    """ISO timestamp for audit and outbox processing."""
    source: str
    """Audit source label."""
    managed_groups: frozenset[str]
    """Unix groups this sync is allowed to inspect and mutate."""
    process_outbox: bool = True
    """Whether retryable group outbox rows should be marked after sync."""
    outbox_limit: int = 1000
    """Maximum group outbox rows to process."""


@dataclass(frozen=True, kw_only=True, slots=True)
class UnixGroupSyncResult:
    """Result of one Unix group reconciliation."""

    dry_run: bool
    """Whether the sync only planned changes."""
    planned_grants: int
    """Number of missing memberships that should be granted."""
    planned_revokes: int
    """Number of memberships that should be revoked."""
    applied_grants: int
    """Number of helper-backed grants applied."""
    applied_revokes: int
    """Number of helper-backed revokes applied."""
    processed_outbox_count: int
    """Number of group outbox rows marked processed."""


class UnixGroupBackend(Protocol):
    """Boundary for reading and mutating Unix group membership."""

    def list_members(self, group_name: str) -> frozenset[str]:
        """Return current members for one Unix group."""
        ...

    def grant(self, handle: str, group_name: str) -> None:
        """Grant one handle to one Unix group."""
        ...

    def revoke(self, handle: str, group_name: str) -> None:
        """Remove one handle from one Unix group."""
        ...


type UnixGroupCommandRunner = Callable[[UnixGroupCommand], UnixGroupCommandResult]


class SubprocessUnixGroupBackend:
    """Unix group backend that delegates mutation to configured commands."""

    def __init__(
        self,
        *,
        grant_command: tuple[str, ...] | None = None,
        revoke_command: tuple[str, ...] | None = None,
        command_runner: UnixGroupCommandRunner | None = None,
    ) -> None:
        self._grant_command = grant_command
        self._revoke_command = revoke_command
        self._command_runner = command_runner or _run_unix_group_command

    def list_members(self, group_name: str) -> frozenset[str]:
        """Return current members for one Unix group."""
        _require_safe_name("group", group_name)
        try:
            group_record = grp.getgrnam(group_name)
        except KeyError:
            return frozenset()
        primary_members = frozenset(
            user_record.pw_name
            for user_record in pwd.getpwall()
            if user_record.pw_gid == group_record.gr_gid
        )
        return frozenset(group_record.gr_mem) | primary_members

    def grant(self, handle: str, group_name: str) -> None:
        """Grant one handle to one Unix group through the configured command."""
        self._run_command(_required_command(self._grant_command, "grant"), handle, group_name)

    def revoke(self, handle: str, group_name: str) -> None:
        """Remove one handle from one Unix group through the configured command."""
        self._run_command(_required_command(self._revoke_command, "revoke"), handle, group_name)

    def _run_command(self, command: tuple[str, ...], handle: str, group_name: str) -> None:
        _require_safe_name("handle", handle)
        _require_safe_name("group", group_name)
        try:
            command_result = self._command_runner(
                UnixGroupCommand(arguments=(*command, handle, group_name)),
            )
        except subprocess.TimeoutExpired as timeout_error:
            raise UnixGroupSyncError(
                _group_command_timeout_message(timeout_error.timeout, handle, group_name),
            ) from timeout_error
        if command_result.return_code != 0:
            raise UnixGroupSyncError(
                f"group command failed for {handle}:{group_name}: {command_result.stderr.strip()}",
            )


def sync_unix_groups(
    database_connection: sqlite3.Connection,
    options: UnixGroupSyncOptions,
    backend: UnixGroupBackend,
) -> UnixGroupSyncResult:
    """Reconcile Unix groups from SQLite group intent only."""
    outbox_item_ids = _retryable_group_outbox_item_ids(database_connection, options)
    try:
        outbox_items = _retryable_group_outbox_items(database_connection, options)
        _validate_group_outbox_items(outbox_items)
        group_grants = list_all_group_grants(database_connection)
        _require_managed_group_grants(group_grants, options.managed_groups)
        changes = _planned_changes(group_grants, backend)
        if options.dry_run:
            return _sync_result(options.dry_run, changes, (), 0)
        applied_changes = _apply_changes(database_connection, options, changes, backend)
        with database_connection:
            processed_outbox_count = _mark_outbox_processed(
                database_connection,
                options,
                outbox_items,
            )
        return _sync_result(options.dry_run, changes, applied_changes, processed_outbox_count)
    except (RepositoryError, UnixGroupSyncError) as error:
        _mark_outbox_failed(database_connection, outbox_item_ids)
        if isinstance(error, RepositoryError):
            raise UnixGroupSyncError(str(error)) from error
        raise


def _planned_changes(
    group_grants: list[GroupGrant],
    backend: UnixGroupBackend,
) -> tuple[UnixGroupChange, ...]:
    members_by_group_name = {
        group_name: backend.list_members(group_name)
        for group_name in sorted({group_grant.group_name for group_grant in group_grants})
    }
    changes: list[UnixGroupChange] = []
    for group_grant in group_grants:
        is_member = group_grant.handle in members_by_group_name[group_grant.group_name]
        if group_grant.intended_state == "present" and not is_member:
            changes.append(_change_from_grant(group_grant))
        if group_grant.intended_state == "absent" and is_member:
            changes.append(_change_from_grant(group_grant))
    return tuple(changes)


def _require_managed_group_grants(
    group_grants: list[GroupGrant],
    managed_groups: frozenset[str],
) -> None:
    if not managed_groups:
        raise UnixGroupSyncError("managed Unix groups are required")
    for group_name in sorted({group_grant.group_name for group_grant in group_grants}):
        if group_name not in managed_groups:
            raise UnixGroupSyncError(f"unmanaged Unix group: {group_name}")


def _change_from_grant(group_grant: GroupGrant) -> UnixGroupChange:
    return UnixGroupChange(
        handle=group_grant.handle,
        group_name=group_grant.group_name,
        intended_state=group_grant.intended_state,
        reason=group_grant.reason,
    )


def _apply_changes(
    database_connection: sqlite3.Connection,
    options: UnixGroupSyncOptions,
    changes: tuple[UnixGroupChange, ...],
    backend: UnixGroupBackend,
) -> tuple[UnixGroupChange, ...]:
    applied_changes: list[UnixGroupChange] = []
    for change in changes:
        match change.intended_state:
            case "present":
                backend.grant(change.handle, change.group_name)
            case "absent":
                backend.revoke(change.handle, change.group_name)
        applied_changes.append(change)
        with database_connection:
            _append_group_sync_audit_event(database_connection, options, change)
    return tuple(applied_changes)


def _append_group_sync_audit_event(
    database_connection: sqlite3.Connection,
    options: UnixGroupSyncOptions,
    change: UnixGroupChange,
) -> None:
    append_audit_event(
        database_connection,
        AuditEvent(
            event_type="group_sync_applied",
            handle=change.handle,
            source=options.source,
            created_at=options.synced_at,
            payload={
                "group_name": change.group_name,
                "intended_state": change.intended_state,
                "reason": change.reason,
            },
        ),
    )


def _retryable_group_outbox_items(
    database_connection: sqlite3.Connection,
    options: UnixGroupSyncOptions,
) -> list[OutboxItem]:
    if options.dry_run or not options.process_outbox:
        return []
    return list_retryable_outbox_items_by_kind(
        database_connection,
        GROUP_SYNC_OUTBOX_KIND,
        options.outbox_limit,
    )


def _retryable_group_outbox_item_ids(
    database_connection: sqlite3.Connection,
    options: UnixGroupSyncOptions,
) -> tuple[int, ...]:
    if options.dry_run or not options.process_outbox:
        return ()
    return list_retryable_outbox_item_ids_by_kind(
        database_connection,
        GROUP_SYNC_OUTBOX_KIND,
        options.outbox_limit,
    )


def _validate_group_outbox_items(outbox_items: list[OutboxItem]) -> None:
    try:
        for outbox_item in outbox_items:
            validate_group_sync_outbox_item(outbox_item)
    except RepositoryError as error:
        raise UnixGroupSyncError(str(error)) from error


def _mark_outbox_processed(
    database_connection: sqlite3.Connection,
    options: UnixGroupSyncOptions,
    outbox_items: list[OutboxItem],
) -> int:
    for outbox_item in outbox_items:
        if outbox_item.id is None:
            raise UnixGroupSyncError("group outbox row has no id")
        mark_outbox_item_processed(database_connection, outbox_item.id, options.synced_at)
    return len(outbox_items)


def _mark_outbox_failed(
    database_connection: sqlite3.Connection,
    outbox_item_ids: tuple[int, ...],
) -> None:
    with database_connection:
        for outbox_item_id in outbox_item_ids:
            mark_outbox_item_failed(database_connection, outbox_item_id)


def _sync_result(
    dry_run: bool,
    planned_changes: tuple[UnixGroupChange, ...],
    applied_changes: tuple[UnixGroupChange, ...],
    processed_outbox_count: int,
) -> UnixGroupSyncResult:
    return UnixGroupSyncResult(
        dry_run=dry_run,
        planned_grants=_count_changes(planned_changes, "present"),
        planned_revokes=_count_changes(planned_changes, "absent"),
        applied_grants=_count_changes(applied_changes, "present"),
        applied_revokes=_count_changes(applied_changes, "absent"),
        processed_outbox_count=processed_outbox_count,
    )


def _count_changes(
    changes: tuple[UnixGroupChange, ...],
    intended_state: GroupIntendedState,
) -> int:
    return sum(1 for change in changes if change.intended_state == intended_state)


def _run_unix_group_command(command: UnixGroupCommand) -> UnixGroupCommandResult:
    completed_process = subprocess.run(  # noqa: S603
        command.arguments,
        capture_output=True,
        check=False,
        text=True,
        timeout=UNIX_GROUP_COMMAND_TIMEOUT_SECONDS,
    )
    return UnixGroupCommandResult(
        return_code=completed_process.returncode,
        stdout=completed_process.stdout,
        stderr=completed_process.stderr,
    )


def _group_command_timeout_message(
    timeout_seconds: float,
    handle: str,
    group_name: str,
) -> str:
    return f"group command timed out after {timeout_seconds:g} seconds for {handle}:{group_name}"


def _required_command(command: tuple[str, ...] | None, operation: str) -> tuple[str, ...]:
    if not command:
        raise UnixGroupSyncError(f"{operation} command is required to apply Unix groups")
    return command


def _require_safe_name(label: str, name: str) -> None:
    if not is_safe_unix_name(name):
        raise UnixGroupSyncError(f"unsafe Unix {label}: {name}")
