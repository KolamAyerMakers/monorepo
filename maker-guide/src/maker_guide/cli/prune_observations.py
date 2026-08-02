"""Command observation retention cleanup command."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Annotated, cast

import typer
from rich.console import Console

from maker_guide.config import DEFAULT_CONFIG_PATH, ConfigError, load_database_path
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG
from maker_guide.repositories.helpers import connect_database
from maker_guide.retention import ObservationRetentionResult, prune_command_observations

app = typer.Typer(
    add_completion=False,
    help="Prune raw shell observations after the course retention window.",
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
def prune(
    *,
    configuration_path: Annotated[
        Path,
        typer.Option("--config", help="Path to the daemon TOML configuration."),
    ] = DEFAULT_CONFIG_PATH,
    database_path: Annotated[
        Path | None,
        typer.Option("--database", help="Override the configured SQLite database path."),
    ] = None,
    today: Annotated[
        str | None,
        typer.Option("--today", help="Override the UTC cleanup date for tests."),
    ] = None,
) -> None:
    """Prune raw command observations when retention has expired."""
    try:
        retention_result = _prune_from_options(configuration_path, database_path, today)
    except (ConfigError, sqlite3.Error) as error:
        Console(stderr=True).print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error

    Console().print(_summary_message(retention_result))


def _prune_from_options(
    configuration_path: Path,
    database_path: Path | None,
    today: str | None,
) -> ObservationRetentionResult:
    with connect_database(
        _database_path_from_options(configuration_path, database_path),
    ) as database_connection:
        return prune_command_observations(
            database_connection,
            DEFAULT_CATALOG,
            _cleanup_date(today),
        )


def _database_path_from_options(configuration_path: Path, database_path: Path | None) -> Path:
    if database_path is not None:
        return database_path.expanduser()
    return load_database_path(configuration_path)


def _cleanup_date(today: str | None) -> date:
    if today is None:
        return datetime.now(UTC).date()
    try:
        return date.fromisoformat(today)
    except ValueError as error:
        raise ConfigError("--today must be an ISO date like 2026-11-30") from error


def _summary_message(retention_result: ObservationRetentionResult) -> str:
    if retention_result.cleanup_due:
        return (
            f"Deleted {retention_result.deleted_count} command observations "
            f"before {retention_result.cutoff_at}."
        )
    return f"Retention window still active until {retention_result.cutoff_at}; deleted 0 rows."
