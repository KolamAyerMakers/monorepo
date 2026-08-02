"""Operational status and recovery checks."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, cast

import typer
from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory
from rich.console import Console

from maker_guide.config import DEFAULT_CONFIG_PATH, ConfigError, load_database_path
from maker_guide.projections.makers import MAKERS_PROJECTION_NAME, MAKERS_PROJECTION_VERSION
from maker_guide.repositories.audit_event import count_unexported_audit_events
from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.outbox_item import (
    OutboxItemCount,
    count_outbox_items_by_kind_and_status,
)
from maker_guide.repositories.projection_version import ProjectionVersion, get_projection_version
from maker_guide.repositories.quest_attempt import count_quest_attempts_by_failure_reason

app = typer.Typer(
    add_completion=False,
    help="Inspect maker-guide operational recovery state.",
    pretty_exceptions_enable=False,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class OperationalStatus:
    """Read-only operational status derived from SQLite."""

    database_path: Path
    """SQLite database path inspected by this status run."""
    sqlite_integrity_results: tuple[str, ...]
    """Rows returned by SQLite PRAGMA integrity_check."""
    migration_revision: str | None
    """Alembic revision recorded in SQLite, if present."""
    migration_head: str
    """Packaged Alembic head revision expected by this release."""
    unexported_audit_events: int
    """Number of audit rows still awaiting JSONL export."""
    unsupported_validation_attempts: int
    """Number of quest attempts that hit the impossible unsupported-validation path."""
    outbox_counts: tuple[OutboxItemCount, ...]
    """Outbox rows grouped by worker kind and processing status."""
    makers_projection: ProjectionVersion | None
    """Last `/makers` projection write metadata, if present."""


def run(arguments: Sequence[str] | None = None) -> int:
    """Run the Typer app for tests."""
    result = cast(
        "object",
        app(
            args=list(arguments) if arguments is not None else None,
            standalone_mode=False,
        ),
    )
    if isinstance(result, int):
        return result
    return 0


@app.command()
def status(
    *,
    configuration_path: Annotated[
        Path,
        typer.Option("--config", help="Path to the daemon TOML configuration."),
    ] = DEFAULT_CONFIG_PATH,
    database_path: Annotated[
        Path | None,
        typer.Option("--database", help="Override the configured SQLite database path."),
    ] = None,
) -> None:
    """Print recovery-relevant operational state."""
    try:
        Console().out(_status_message(_status_from_options(configuration_path, database_path)))
    except (ConfigError, sqlite3.Error) as error:
        Console(stderr=True).print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error


@app.command()
def check(
    *,
    configuration_path: Annotated[
        Path,
        typer.Option("--config", help="Path to the daemon TOML configuration."),
    ] = DEFAULT_CONFIG_PATH,
    database_path: Annotated[
        Path | None,
        typer.Option("--database", help="Override the configured SQLite database path."),
    ] = None,
    max_unexported_audit_events: Annotated[
        int,
        typer.Option(
            "--max-unexported-audit-events",
            min=0,
            help="Maximum acceptable audit export backlog.",
        ),
    ] = 0,
) -> None:
    """Exit nonzero when recovery-relevant state needs attention."""
    try:
        issues = _check_from_options(
            configuration_path,
            database_path,
            max_unexported_audit_events,
        )
    except (ConfigError, sqlite3.Error) as error:
        Console(stderr=True).print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error

    if issues:
        error_console = Console(stderr=True)
        error_console.print("[red]Operational check failed:[/red]")
        for issue in issues:
            error_console.print(f"[red]- {issue}[/red]")
        raise typer.Exit(1)
    Console().print("Operational checks passed.")


def _status_from_options(
    configuration_path: Path,
    database_path: Path | None,
) -> OperationalStatus:
    resolved_database_path = _database_path_from_options(configuration_path, database_path)
    with connect_database(resolved_database_path) as database_connection:
        return OperationalStatus(
            database_path=resolved_database_path,
            sqlite_integrity_results=_sqlite_integrity_check(database_connection),
            migration_revision=_migration_revision(database_connection),
            migration_head=_migration_head(),
            unexported_audit_events=count_unexported_audit_events(database_connection),
            unsupported_validation_attempts=count_quest_attempts_by_failure_reason(
                database_connection,
                "unsupported-validation",
            ),
            outbox_counts=tuple(count_outbox_items_by_kind_and_status(database_connection)),
            makers_projection=get_projection_version(database_connection, MAKERS_PROJECTION_NAME),
        )


def _check_from_options(
    configuration_path: Path,
    database_path: Path | None,
    max_unexported_audit_events: int,
) -> tuple[str, ...]:
    if max_unexported_audit_events < 0:
        raise ConfigError("max unexported audit events must be non-negative")
    return _check_issues(
        _status_from_options(configuration_path, database_path),
        max_unexported_audit_events,
    )


def _check_issues(
    operational_status: OperationalStatus,
    max_unexported_audit_events: int,
) -> tuple[str, ...]:
    issues: list[str] = []
    migration_revision = operational_status.migration_revision
    migration_head = operational_status.migration_head
    if operational_status.sqlite_integrity_results != ("ok",):
        issues.append(
            "".join(
                (
                    "SQLite integrity check failed: ",
                    _integrity_label(operational_status.sqlite_integrity_results),
                ),
            ),
        )
    if migration_revision is None:
        issues.append("migration revision is missing; inspect with maker-guide-db current")
    elif migration_revision != migration_head:
        issues.append(
            f"migration revision is {migration_revision}; expected {migration_head}",
        )
    if operational_status.unexported_audit_events > max_unexported_audit_events:
        issues.append(
            "".join(
                (
                    f"audit export backlog is {operational_status.unexported_audit_events}; ",
                    f"maximum is {max_unexported_audit_events}",
                ),
            ),
        )
    if operational_status.unsupported_validation_attempts:
        issues.append(
            "".join(
                (
                    "unsupported validation attempts: ",
                    str(operational_status.unsupported_validation_attempts),
                ),
            ),
        )
    issues.extend(
        f"outbox backlog {outbox_count.kind}/{outbox_count.status} has {outbox_count.count} rows"
        for outbox_count in operational_status.outbox_counts
        if outbox_count.status != "processed"
    )
    if operational_status.makers_projection is None:
        issues.append("makers projection is missing; run maker-guide-sync-derived-data")
    elif operational_status.makers_projection.version != MAKERS_PROJECTION_VERSION:
        issues.append(
            "".join(
                (
                    "makers projection version is ",
                    str(operational_status.makers_projection.version),
                    "; ",
                    f"expected {MAKERS_PROJECTION_VERSION}",
                ),
            ),
        )
    return tuple(issues)


def _status_message(operational_status: OperationalStatus) -> str:
    return "\n".join(_status_lines(operational_status))


def _status_lines(operational_status: OperationalStatus) -> tuple[str, ...]:
    lines = [
        f"database_path={operational_status.database_path}",
        f"sqlite_integrity={_integrity_label(operational_status.sqlite_integrity_results)}",
        f"migration_revision={operational_status.migration_revision or 'missing'}",
        f"migration_head={operational_status.migration_head}",
        f"audit_unexported={operational_status.unexported_audit_events}",
        f"unsupported_validation_attempts={operational_status.unsupported_validation_attempts}",
    ]
    if operational_status.outbox_counts:
        lines.extend(
            _outbox_count_line(outbox_count) for outbox_count in operational_status.outbox_counts
        )
    else:
        lines.append("outbox=none")
    lines.append(_makers_projection_line(operational_status.makers_projection))
    lines.append(
        f"migration_state_command=maker-guide-db --config {DEFAULT_CONFIG_PATH} current",
    )
    return tuple(lines)


def _sqlite_integrity_check(database_connection: sqlite3.Connection) -> tuple[str, ...]:
    integrity_records = cast(
        "list[tuple[str]]",
        database_connection.execute("pragma integrity_check").fetchall(),
    )
    return tuple(integrity_record[0] for integrity_record in integrity_records)


def _migration_revision(database_connection: sqlite3.Connection) -> str | None:
    try:
        revision_record = cast(
            "tuple[str] | None",
            database_connection.execute("select version_num from alembic_version").fetchone(),
        )
    except sqlite3.OperationalError:
        return None
    if revision_record is None:
        return None
    return revision_record[0]


def _migration_head() -> str:
    return str(ScriptDirectory.from_config(_alembic_config()).get_current_head())


def _alembic_config() -> AlembicConfig:
    package_directory = Path(__file__).resolve().parents[1]
    if (package_directory / "alembic.ini").is_file():
        alembic_config = AlembicConfig(package_directory / "alembic.ini")
        alembic_config.set_main_option("script_location", str(package_directory / "migrations"))
        return alembic_config
    raise ConfigError("packaged alembic.ini is missing")


def _integrity_label(sqlite_integrity_results: tuple[str, ...]) -> str:
    if not sqlite_integrity_results:
        return "missing"
    return " | ".join(sqlite_integrity_results)


def _outbox_count_line(outbox_count: OutboxItemCount) -> str:
    return " ".join(
        (
            f"outbox kind={outbox_count.kind}",
            f"status={outbox_count.status}",
            f"count={outbox_count.count}",
        ),
    )


def _makers_projection_line(makers_projection: ProjectionVersion | None) -> str:
    if makers_projection is None:
        return f"makers_projection=missing expected_version={MAKERS_PROJECTION_VERSION}"
    return " ".join(
        (
            f"makers_projection=version:{makers_projection.version}",
            f"expected_version:{MAKERS_PROJECTION_VERSION}",
            f"last_written_at:{makers_projection.last_written_at}",
        ),
    )


def _database_path_from_options(configuration_path: Path, database_path: Path | None) -> Path:
    if database_path is not None:
        return database_path.expanduser()
    return load_database_path(configuration_path)
