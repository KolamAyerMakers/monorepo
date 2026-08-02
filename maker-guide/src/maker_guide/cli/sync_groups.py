"""Unix group synchronization command."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, cast

import typer
from rich.console import Console

from maker_guide.config import (
    DEFAULT_CONFIG_PATH,
    ConfigError,
    UnixGroupsConfig,
    load_database_path,
    load_unix_groups_config,
)
from maker_guide.repositories.helpers import connect_database
from maker_guide.unix_groups import (
    SubprocessUnixGroupBackend,
    UnixGroupBackend,
    UnixGroupSyncError,
    UnixGroupSyncOptions,
    UnixGroupSyncResult,
    sync_unix_groups,
)
from maker_guide.unix_names import is_allowed_managed_group_name

app = typer.Typer(
    add_completion=False,
    help="Synchronize Unix groups from SQLite group intent.",
    pretty_exceptions_enable=False,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class GroupSyncCommandDependencies:
    """Dependencies injected into the group sync command."""

    backend: UnixGroupBackend | None = None
    """Backend used instead of reading and mutating real Unix groups."""


@dataclass(frozen=True, kw_only=True, slots=True)
class _MutationCommands:
    """Resolved commands for applying group mutations."""

    grant_command: tuple[str, ...] | None
    """Command prefix that grants one user to one group."""
    revoke_command: tuple[str, ...] | None
    """Command prefix that revokes one user from one group."""


@dataclass(frozen=True, kw_only=True, slots=True)
class _SyncInvocation:
    """Resolved CLI inputs for one group sync run."""

    context: typer.Context
    """Typer context carrying injected dependencies."""
    configuration_path: Path
    """Path to the daemon TOML configuration."""
    database_path: Path | None
    """Optional database path override."""
    apply_changes: bool
    """Whether to apply command-backed mutations."""
    process_outbox: bool
    """Whether to process group outbox rows after a successful apply."""
    managed_groups: tuple[str, ...]
    """Managed groups passed explicitly on the CLI."""


def run(
    arguments: Sequence[str] | None = None,
    backend: UnixGroupBackend | None = None,
) -> int:
    """Run the Typer app for tests."""
    result = cast(
        "object",
        app(
            args=list(arguments) if arguments is not None else None,
            standalone_mode=False,
            obj=GroupSyncCommandDependencies(backend=backend),
        ),
    )
    if isinstance(result, int):
        return result
    return 0


@app.command()
def sync(  # noqa: PLR0913
    context: typer.Context,
    *,
    configuration_path: Annotated[
        Path,
        typer.Option("--config", help="Path to the daemon TOML configuration."),
    ] = DEFAULT_CONFIG_PATH,
    database_path: Annotated[
        Path | None,
        typer.Option("--database", help="Override the configured SQLite database path."),
    ] = None,
    apply_changes: Annotated[
        bool,
        typer.Option("--apply/--dry-run", help="Apply planned Unix group mutations."),
    ] = False,
    managed_groups: Annotated[
        list[str] | None,
        typer.Option(
            "--managed-group",
            help="Allowed Unix group; repeat for multiple groups.",
        ),
    ] = None,
    process_outbox: Annotated[
        bool,
        typer.Option(
            "--process-outbox/--skip-outbox",
            help="Mark retryable group outbox rows after a successful apply.",
        ),
    ] = True,
) -> None:
    """Reconcile system Unix groups from SQLite intent."""
    try:
        sync_result = _sync_from_options(
            _SyncInvocation(
                context=context,
                configuration_path=configuration_path,
                database_path=database_path,
                apply_changes=apply_changes,
                process_outbox=process_outbox,
                managed_groups=tuple(managed_groups or ()),
            ),
        )
    except (ConfigError, UnixGroupSyncError, sqlite3.Error) as error:
        Console(stderr=True).print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error

    Console().print(_summary_message(sync_result))


def _sync_from_options(sync_invocation: _SyncInvocation) -> UnixGroupSyncResult:
    injected_backend = _backend_from_context(sync_invocation.context)
    unix_groups_configuration = _unix_groups_configuration(sync_invocation.configuration_path)
    mutation_commands = _mutation_commands_from_config(
        unix_groups_configuration,
        sync_invocation.apply_changes and injected_backend is None,
    )
    with connect_database(
        _database_path_from_options(
            sync_invocation.configuration_path,
            sync_invocation.database_path,
        ),
    ) as connection:
        return sync_unix_groups(
            connection,
            UnixGroupSyncOptions(
                dry_run=not sync_invocation.apply_changes,
                synced_at=_utc_timestamp(),
                source="maker-guide-sync-groups",
                managed_groups=_managed_groups_from_options(
                    unix_groups_configuration,
                    sync_invocation.managed_groups,
                ),
                process_outbox=sync_invocation.process_outbox and sync_invocation.apply_changes,
            ),
            injected_backend
            or SubprocessUnixGroupBackend(
                grant_command=mutation_commands.grant_command,
                revoke_command=mutation_commands.revoke_command,
            ),
        )


def _mutation_commands_from_config(
    unix_groups_configuration: UnixGroupsConfig | None,
    apply_changes: bool,
) -> _MutationCommands:
    if unix_groups_configuration is None:
        mutation_commands = _MutationCommands(grant_command=None, revoke_command=None)
    else:
        mutation_commands = _MutationCommands(
            grant_command=unix_groups_configuration.grant_command,
            revoke_command=unix_groups_configuration.revoke_command,
        )
    if not apply_changes:
        return mutation_commands
    if mutation_commands.grant_command is None or mutation_commands.revoke_command is None:
        raise ConfigError("unix group commands are required when applying changes")
    return mutation_commands


def _unix_groups_configuration(configuration_path: Path) -> UnixGroupsConfig | None:
    if configuration_path.is_file():
        return load_unix_groups_config(configuration_path)
    return None


def _managed_groups_from_options(
    unix_groups_configuration: UnixGroupsConfig | None,
    managed_groups: tuple[str, ...],
) -> frozenset[str]:
    if managed_groups:
        return _validated_managed_groups(managed_groups)
    if unix_groups_configuration is not None:
        return unix_groups_configuration.managed_groups
    return frozenset()


def _validated_managed_groups(managed_groups: tuple[str, ...]) -> frozenset[str]:
    if len(set(managed_groups)) != len(managed_groups):
        raise ConfigError("managed groups must not contain duplicates")
    for group_name in managed_groups:
        if not is_allowed_managed_group_name(group_name):
            raise ConfigError(f"managed group is unsafe: {group_name}")
    return frozenset(managed_groups)


def _database_path_from_options(configuration_path: Path, database_path: Path | None) -> Path:
    if database_path is not None:
        return database_path.expanduser()
    return load_database_path(configuration_path)


def _summary_message(sync_result: UnixGroupSyncResult) -> str:
    mode = "Dry run" if sync_result.dry_run else "Applied"
    return "; ".join(
        (
            f"{mode}: planned {sync_result.planned_grants} grants",
            f"planned {sync_result.planned_revokes} revokes",
            f"applied {sync_result.applied_grants} grants",
            f"applied {sync_result.applied_revokes} revokes",
            f"processed {sync_result.processed_outbox_count} group outbox rows.",
        ),
    )


def _backend_from_context(context: typer.Context) -> UnixGroupBackend | None:
    context_object = cast("object", context.obj)
    if isinstance(context_object, GroupSyncCommandDependencies):
        return context_object.backend
    return None


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
