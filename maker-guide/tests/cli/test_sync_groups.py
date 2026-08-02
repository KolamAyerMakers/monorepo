"""Tests for Unix group synchronization CLI."""

from __future__ import annotations

from pathlib import Path

from maker_guide.cli.sync_groups import run
from maker_guide.repositories.group_grant import GroupGrant, upsert_group_grant
from maker_guide.repositories.helpers import connect_database
from tests.repositories.helpers import TIMESTAMP, write_learner


def test_sync_groups_cli_dry_run_uses_database_without_helpers(
    migrated_database_path: Path,
) -> None:
    """Dry-run can inspect SQLite intent without configured privileged helpers."""
    backend = _RecordingUnixGroupBackend(members_by_group_name={"makers": frozenset()})
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        upsert_group_grant(database_connection, _group_grant())

    assert (
        run(
            ["--database", str(migrated_database_path), "--managed-group", "makers"],
            backend=backend,
        )
        == 0
    )
    assert backend.operations == []


def test_sync_groups_cli_apply_uses_injected_backend(
    migrated_database_path: Path,
) -> None:
    """Apply mode can be tested without real Unix group mutation."""
    backend = _RecordingUnixGroupBackend(members_by_group_name={"makers": frozenset()})
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        upsert_group_grant(database_connection, _group_grant())

    assert (
        run(
            [
                "--database",
                str(migrated_database_path),
                "--managed-group",
                "makers",
                "--apply",
            ],
            backend=backend,
        )
        == 0
    )
    assert backend.operations == [("grant", "alice", "makers")]


def test_sync_groups_cli_apply_requires_commands_without_injected_backend(
    migrated_database_path: Path,
) -> None:
    """Real apply needs configured command arrays."""
    assert (
        run(
            ["--database", str(migrated_database_path), "--managed-group", "makers", "--apply"],
        )
        == 1
    )


def test_sync_groups_cli_rejects_unmanaged_group(migrated_database_path: Path) -> None:
    """CLI rejects SQLite intent outside the managed group allowlist."""
    backend = _RecordingUnixGroupBackend(members_by_group_name={"sudo": frozenset()})
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        upsert_group_grant(
            database_connection,
            GroupGrant(
                handle="alice",
                group_name="sudo",
                intended_state="present",
                reason="test",
                updated_at=TIMESTAMP,
            ),
        )

    assert (
        run(
            ["--database", str(migrated_database_path), "--managed-group", "makers"],
            backend=backend,
        )
        == 1
    )
    assert backend.operations == []


class _RecordingUnixGroupBackend:
    def __init__(self, *, members_by_group_name: dict[str, frozenset[str]]) -> None:
        self.members_by_group_name = members_by_group_name
        self.operations: list[tuple[str, str, str]] = []

    def list_members(self, group_name: str) -> frozenset[str]:
        return self.members_by_group_name.get(group_name, frozenset())

    def grant(self, handle: str, group_name: str) -> None:
        self.operations.append(("grant", handle, group_name))

    def revoke(self, handle: str, group_name: str) -> None:
        self.operations.append(("revoke", handle, group_name))


def _group_grant() -> GroupGrant:
    return GroupGrant(
        handle="alice",
        group_name="makers",
        intended_state="present",
        reason="tier",
        updated_at=TIMESTAMP,
    )
