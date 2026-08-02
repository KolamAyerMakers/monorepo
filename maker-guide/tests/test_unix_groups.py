"""Tests for Unix group reconciliation."""

from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path
from typing import cast

import pytest

from maker_guide.repositories.audit_event import list_unexported_audit_events
from maker_guide.repositories.group_grant import GroupGrant, GroupIntendedState, upsert_group_grant
from maker_guide.repositories.helpers import connect_database, dump_json
from maker_guide.repositories.learner import Learner, upsert_learner
from maker_guide.repositories.outbox_item import (
    FAILED_OUTBOX_STATUS,
    GROUP_SYNC_OUTBOX_KIND,
    PENDING_OUTBOX_STATUS,
    OutboxItem,
    enqueue_outbox_item,
    group_sync_outbox_item,
    list_retryable_outbox_items_by_kind,
)
from maker_guide.unix_groups import (
    SubprocessUnixGroupBackend,
    UnixGroupCommand,
    UnixGroupCommandResult,
    UnixGroupSyncError,
    UnixGroupSyncOptions,
    sync_unix_groups,
)
from tests.repositories.helpers import TIMESTAMP, write_learner


def test_unix_group_sync_dry_run_plans_without_mutation(
    migrated_database_path: Path,
) -> None:
    """Dry-run mode reports drift without calling mutation helpers or processing outbox."""
    backend = _FakeUnixGroupBackend(members_by_group_name={"makers": frozenset()})
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        upsert_group_grant(database_connection, _group_grant("alice", "makers", "present"))
        enqueue_outbox_item(database_connection, _group_outbox_item())

        result = sync_unix_groups(
            database_connection,
            UnixGroupSyncOptions(
                dry_run=True,
                synced_at=TIMESTAMP,
                source="test",
                managed_groups=frozenset({"makers"}),
            ),
            backend,
        )

        assert result.planned_grants == 1
        assert result.planned_revokes == 0
        assert result.applied_grants == 0
        assert backend.operations == []
        assert [
            outbox_item.status
            for outbox_item in list_retryable_outbox_items_by_kind(
                database_connection,
                GROUP_SYNC_OUTBOX_KIND,
                10,
            )
        ] == ["pending"]


def test_unix_group_sync_applies_explicit_grants_and_revokes(
    migrated_database_path: Path,
) -> None:
    """Apply mode mutates only memberships represented by SQLite intent."""
    backend = _FakeUnixGroupBackend(members_by_group_name={"makers": frozenset({"bob"})})
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        _write_learner(database_connection, "bob")
        upsert_group_grant(database_connection, _group_grant("alice", "makers", "present"))
        upsert_group_grant(database_connection, _group_grant("bob", "makers", "absent"))
        enqueue_outbox_item(database_connection, _group_outbox_item())

        result = sync_unix_groups(
            database_connection,
            UnixGroupSyncOptions(
                dry_run=False,
                synced_at=TIMESTAMP,
                source="test",
                managed_groups=frozenset({"makers"}),
            ),
            backend,
        )

        assert backend.operations == [
            ("grant", "alice", "makers"),
            ("revoke", "bob", "makers"),
        ]
        assert result.applied_grants == 1
        assert result.applied_revokes == 1
        assert result.processed_outbox_count == 1
        assert [
            event.event_type for event in list_unexported_audit_events(database_connection, 10)
        ] == ["group_sync_applied", "group_sync_applied"]
        assert (
            list_retryable_outbox_items_by_kind(
                database_connection,
                GROUP_SYNC_OUTBOX_KIND,
                10,
            )
            == []
        )


def test_unix_group_sync_ignores_memberships_without_sqlite_intent(
    migrated_database_path: Path,
) -> None:
    """Actual Unix group members not represented in SQLite are not treated as progress."""
    backend = _FakeUnixGroupBackend(members_by_group_name={"makers": frozenset({"alice", "bob"})})
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        upsert_group_grant(database_connection, _group_grant("alice", "makers", "present"))

        result = sync_unix_groups(
            database_connection,
            UnixGroupSyncOptions(
                dry_run=False,
                synced_at=TIMESTAMP,
                source="test",
                managed_groups=frozenset({"makers"}),
            ),
            backend,
        )

        assert backend.operations == []
        assert result.planned_grants == 0
        assert result.planned_revokes == 0


def test_unix_group_sync_marks_outbox_failed_when_helper_fails(
    migrated_database_path: Path,
) -> None:
    """Failed helper mutation leaves group sync work retryable."""
    backend = _FakeUnixGroupBackend(
        members_by_group_name={"makers": frozenset()},
        failing_operation="grant",
    )
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        upsert_group_grant(database_connection, _group_grant("alice", "makers", "present"))
        enqueue_outbox_item(database_connection, _group_outbox_item())

        with pytest.raises(UnixGroupSyncError, match="grant failed"):
            sync_unix_groups(
                database_connection,
                UnixGroupSyncOptions(
                    dry_run=False,
                    synced_at=TIMESTAMP,
                    source="test",
                    managed_groups=frozenset({"makers"}),
                ),
                backend,
            )

        assert [
            outbox_item.status
            for outbox_item in list_retryable_outbox_items_by_kind(
                database_connection,
                GROUP_SYNC_OUTBOX_KIND,
                10,
            )
        ] == ["failed"]


def test_unix_group_sync_audits_successful_partial_apply_before_later_failure(
    migrated_database_path: Path,
) -> None:
    """Successful external mutations keep audit evidence when later mutations fail."""
    backend = _FakeUnixGroupBackend(
        members_by_group_name={"makers": frozenset({"bob"})},
        failing_operation="revoke",
    )
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        _write_learner(database_connection, "bob")
        upsert_group_grant(database_connection, _group_grant("alice", "makers", "present"))
        upsert_group_grant(database_connection, _group_grant("bob", "makers", "absent"))
        enqueue_outbox_item(database_connection, _group_outbox_item())

        with pytest.raises(UnixGroupSyncError, match="revoke failed"):
            sync_unix_groups(
                database_connection,
                UnixGroupSyncOptions(
                    dry_run=False,
                    synced_at=TIMESTAMP,
                    source="test",
                    managed_groups=frozenset({"makers"}),
                ),
                backend,
            )

        assert backend.operations == [("grant", "alice", "makers")]
        assert [
            event.payload for event in list_unexported_audit_events(database_connection, 10)
        ] == [
            {"group_name": "makers", "intended_state": "present", "reason": "tier"},
        ]
        assert [
            outbox_item.status
            for outbox_item in list_retryable_outbox_items_by_kind(
                database_connection,
                GROUP_SYNC_OUTBOX_KIND,
                10,
            )
        ] == [FAILED_OUTBOX_STATUS]

        backend.failing_operation = None
        result = sync_unix_groups(
            database_connection,
            UnixGroupSyncOptions(
                dry_run=False,
                synced_at=TIMESTAMP,
                source="test",
                managed_groups=frozenset({"makers"}),
            ),
            backend,
        )

        assert backend.operations == [
            ("grant", "alice", "makers"),
            ("revoke", "bob", "makers"),
        ]
        assert result.applied_grants == 0
        assert result.applied_revokes == 1
        assert result.processed_outbox_count == 1
        assert [
            event.payload for event in list_unexported_audit_events(database_connection, 10)
        ] == [
            {"group_name": "makers", "intended_state": "present", "reason": "tier"},
            {"group_name": "makers", "intended_state": "absent", "reason": "tier"},
        ]


def test_unix_group_sync_retries_failed_side_effect_from_sqlite(
    migrated_database_path: Path,
) -> None:
    """A failed group side effect after DB commit is repairable from SQLite intent."""
    backend = _FakeUnixGroupBackend(members_by_group_name={"makers": frozenset()})
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        upsert_group_grant(database_connection, _group_grant("alice", "makers", "present"))
        enqueue_outbox_item(database_connection, _group_outbox_item())
        database_connection.execute(
            "update outbox_items set status = 'failed' where kind = ?",
            (GROUP_SYNC_OUTBOX_KIND,),
        )

        result = sync_unix_groups(
            database_connection,
            UnixGroupSyncOptions(
                dry_run=False,
                synced_at=TIMESTAMP,
                source="test",
                managed_groups=frozenset({"makers"}),
            ),
            backend,
        )

        assert backend.operations == [("grant", "alice", "makers")]
        assert result.processed_outbox_count == 1
        assert (
            list_retryable_outbox_items_by_kind(database_connection, GROUP_SYNC_OUTBOX_KIND, 10)
            == []
        )


def test_unix_group_sync_rejects_unmanaged_sqlite_intent_before_backend_access(
    migrated_database_path: Path,
) -> None:
    """Unmanaged group rows are rejected before reading or mutating Unix groups."""
    backend = _FakeUnixGroupBackend(members_by_group_name={"sudo": frozenset()})
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        upsert_group_grant(database_connection, _group_grant("alice", "sudo", "present"))

        with pytest.raises(UnixGroupSyncError, match="unmanaged Unix group: sudo"):
            sync_unix_groups(
                database_connection,
                UnixGroupSyncOptions(
                    dry_run=True,
                    synced_at=TIMESTAMP,
                    source="test",
                    managed_groups=frozenset({"makers"}),
                ),
                backend,
            )

    assert backend.listed_groups == []
    assert backend.operations == []


def test_unix_group_sync_rejects_malformed_group_outbox_before_backend_access(
    migrated_database_path: Path,
) -> None:
    """Group sync validates queued payloads before reading or mutating Unix groups."""
    backend = _FakeUnixGroupBackend(members_by_group_name={"makers": frozenset()})
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        upsert_group_grant(database_connection, _group_grant("alice", "makers", "present"))
        database_connection.execute(
            """
            insert into outbox_items (kind, status, created_at, processed_at, payload_json)
            values (?, ?, ?, ?, ?)
            """,
            (
                GROUP_SYNC_OUTBOX_KIND,
                PENDING_OUTBOX_STATUS,
                TIMESTAMP,
                None,
                dump_json({"handle": "alice", "reason": "group_grant_intended"}),
            ),
        )

        with pytest.raises(UnixGroupSyncError, match="group_sync outbox payload"):
            sync_unix_groups(
                database_connection,
                UnixGroupSyncOptions(
                    dry_run=False,
                    synced_at=TIMESTAMP,
                    source="test",
                    managed_groups=frozenset({"makers"}),
                ),
                backend,
            )

    assert backend.listed_groups == []
    assert backend.operations == []
    with connect_database(migrated_database_path) as database_connection:
        assert [
            outbox_item.status
            for outbox_item in list_retryable_outbox_items_by_kind(
                database_connection,
                GROUP_SYNC_OUTBOX_KIND,
                10,
            )
        ] == [FAILED_OUTBOX_STATUS]


def test_unix_group_sync_marks_non_object_group_outbox_json_failed(
    migrated_database_path: Path,
) -> None:
    """Group sync can fail an undecodable queued row without trusting its payload."""
    backend = _FakeUnixGroupBackend(members_by_group_name={"makers": frozenset()})
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        upsert_group_grant(database_connection, _group_grant("alice", "makers", "present"))
        database_connection.execute(
            """
            insert into outbox_items (kind, status, created_at, processed_at, payload_json)
            values (?, ?, ?, ?, ?)
            """,
            (GROUP_SYNC_OUTBOX_KIND, PENDING_OUTBOX_STATUS, TIMESTAMP, None, "[]"),
        )

        with pytest.raises(UnixGroupSyncError, match="JSON payload must be an object"):
            sync_unix_groups(
                database_connection,
                UnixGroupSyncOptions(
                    dry_run=False,
                    synced_at=TIMESTAMP,
                    source="test",
                    managed_groups=frozenset({"makers"}),
                ),
                backend,
            )

    assert backend.listed_groups == []
    assert backend.operations == []
    with connect_database(migrated_database_path) as database_connection:
        assert database_connection.execute(
            "select status from outbox_items where kind = ?",
            (GROUP_SYNC_OUTBOX_KIND,),
        ).fetchall() == [(FAILED_OUTBOX_STATUS,)]


def test_unix_group_sync_requires_managed_group_allowlist(
    migrated_database_path: Path,
) -> None:
    """Sync fails closed when no managed group allowlist is provided."""
    backend = _FakeUnixGroupBackend(members_by_group_name={"makers": frozenset()})
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        upsert_group_grant(database_connection, _group_grant("alice", "makers", "present"))

        with pytest.raises(UnixGroupSyncError, match="managed Unix groups are required"):
            sync_unix_groups(
                database_connection,
                UnixGroupSyncOptions(
                    dry_run=True,
                    synced_at=TIMESTAMP,
                    source="test",
                    managed_groups=frozenset(),
                ),
                backend,
            )

    assert backend.listed_groups == []
    assert backend.operations == []


def test_subprocess_unix_group_backend_appends_identity_to_configured_commands() -> None:
    """Configured commands are executed as argument arrays with no shell string."""
    commands: list[UnixGroupCommand] = []

    def record_command(command: UnixGroupCommand) -> UnixGroupCommandResult:
        commands.append(command)
        return UnixGroupCommandResult(return_code=0, stdout="", stderr="")

    backend = SubprocessUnixGroupBackend(
        grant_command=("sudo", "-n", "/usr/local/sbin/maker-guide-grant-group"),
        revoke_command=("sudo", "-n", "/usr/local/sbin/maker-guide-revoke-group"),
        command_runner=record_command,
    )

    backend.grant("alice", "makers")
    backend.revoke("alice", "makers")

    assert [command.arguments for command in commands] == [
        ("sudo", "-n", "/usr/local/sbin/maker-guide-grant-group", "alice", "makers"),
        ("sudo", "-n", "/usr/local/sbin/maker-guide-revoke-group", "alice", "makers"),
    ]


def test_subprocess_unix_group_backend_requires_command_before_apply() -> None:
    """Apply mode cannot mutate without an explicit command prefix."""
    with pytest.raises(UnixGroupSyncError, match="grant command is required"):
        SubprocessUnixGroupBackend().grant("alice", "makers")


def test_subprocess_unix_group_backend_times_out_system_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Configured group commands fail fast when the child process hangs."""
    recorded_timeout: list[float | None] = []

    def run_with_timeout(
        arguments: tuple[str, ...],
        *,
        capture_output: bool,
        check: bool,
        text: bool,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        assert capture_output is True
        assert check is False
        assert text is True
        recorded_timeout.append(timeout)
        raise subprocess.TimeoutExpired(arguments, timeout)

    monkeypatch.setattr(subprocess, "run", run_with_timeout)

    backend = SubprocessUnixGroupBackend(grant_command=("grant",), revoke_command=("revoke",))

    with pytest.raises(UnixGroupSyncError, match="timed out after 10 seconds"):
        backend.grant("alice", "makers")
    assert recorded_timeout == [10.0]


class _FakeUnixGroupBackend:
    def __init__(
        self,
        *,
        members_by_group_name: dict[str, frozenset[str]],
        failing_operation: str | None = None,
    ) -> None:
        self.members_by_group_name = members_by_group_name
        self.failing_operation = failing_operation
        self.listed_groups: list[str] = []
        self.operations: list[tuple[str, str, str]] = []

    def list_members(self, group_name: str) -> frozenset[str]:
        self.listed_groups.append(group_name)
        return self.members_by_group_name.get(group_name, frozenset())

    def grant(self, handle: str, group_name: str) -> None:
        if self.failing_operation == "grant":
            raise UnixGroupSyncError("grant failed")
        self.operations.append(("grant", handle, group_name))
        self.members_by_group_name[group_name] = frozenset(
            {*self.members_by_group_name.get(group_name, frozenset()), handle},
        )

    def revoke(self, handle: str, group_name: str) -> None:
        if self.failing_operation == "revoke":
            raise UnixGroupSyncError("revoke failed")
        self.operations.append(("revoke", handle, group_name))
        self.members_by_group_name[group_name] = frozenset(
            member
            for member in self.members_by_group_name.get(group_name, frozenset())
            if member != handle
        )


def _write_learner(database_connection: sqlite3.Connection, handle: str) -> None:
    upsert_learner(
        database_connection,
        Learner(handle=handle, joined_at=TIMESTAMP, tagline=None, created_at=TIMESTAMP),
    )


def _group_grant(handle: str, group_name: str, intended_state: str) -> GroupGrant:
    return GroupGrant(
        handle=handle,
        group_name=group_name,
        intended_state=cast("GroupIntendedState", intended_state),
        reason="tier",
        updated_at=TIMESTAMP,
    )


def _group_outbox_item() -> OutboxItem:
    return group_sync_outbox_item(
        handle="alice",
        course_id="makers",
        group_names=("makers",),
        created_at=TIMESTAMP,
    )
