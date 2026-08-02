"""Audit JSONL export command."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, cast

import typer
from rich.console import Console

from maker_guide.audit_export import (
    AuditExportError,
    AuditExportOptions,
    AuditExportResult,
    export_audit_events,
)
from maker_guide.config import DEFAULT_CONFIG_PATH, ConfigError, load_database_path
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG
from maker_guide.repositories.helpers import connect_database

app = typer.Typer(
    add_completion=False,
    help="Export committed audit events to date-partitioned JSONL.",
    pretty_exceptions_enable=False,
)


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
def export(
    *,
    configuration_path: Annotated[
        Path,
        typer.Option("--config", help="Path to the daemon TOML configuration."),
    ] = DEFAULT_CONFIG_PATH,
    database_path: Annotated[
        Path | None,
        typer.Option("--database", help="Override the configured SQLite database path."),
    ] = None,
    audit_root: Annotated[
        Path,
        typer.Option("--audit-root", help="Directory for date-partitioned JSONL files."),
    ] = Path("/var/lib/maker-guide/audit"),
    limit: Annotated[
        int,
        typer.Option("--limit", min=1, help="Maximum rows to export."),
    ] = 1000,
) -> None:
    """Export committed SQLite audit rows to JSONL."""
    try:
        export_result = _export_from_options(configuration_path, database_path, audit_root, limit)
    except (AuditExportError, ConfigError, sqlite3.Error) as error:
        Console(stderr=True).print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error

    Console().print(_summary_message(export_result))


def _export_from_options(
    configuration_path: Path,
    database_path: Path | None,
    audit_root: Path,
    limit: int,
) -> AuditExportResult:
    with connect_database(
        _database_path_from_options(configuration_path, database_path),
    ) as database_connection:
        return export_audit_events(
            database_connection,
            AuditExportOptions(
                audit_root=audit_root.expanduser(),
                exported_at=_utc_timestamp(),
                timezone=DEFAULT_CATALOG.course.timezone,
                limit=limit,
            ),
        )


def _database_path_from_options(configuration_path: Path, database_path: Path | None) -> Path:
    if database_path is not None:
        return database_path.expanduser()
    return load_database_path(configuration_path)


def _summary_message(export_result: AuditExportResult) -> str:
    return f"Exported {export_result.exported_count} audit events to {export_result.audit_root}."


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
