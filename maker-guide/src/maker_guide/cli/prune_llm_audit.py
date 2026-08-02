"""Restricted LLM audit retention cleanup command."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, cast

import typer
from rich.console import Console

from maker_guide.config import DEFAULT_CONFIG_PATH, ConfigError, load_database_path
from maker_guide.repositories.helpers import connect_database
from maker_guide.retention import LlmAuditRetentionResult, prune_llm_audit_logs

app = typer.Typer(
    add_completion=False,
    help="Prune restricted full LLM audit logs after their retention window.",
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
    now: Annotated[
        str | None,
        typer.Option("--now", help="Override the UTC cleanup timestamp for tests."),
    ] = None,
) -> None:
    """Prune restricted full LLM audit logs whose expiry timestamp has passed."""
    try:
        retention_result = _prune_from_options(configuration_path, database_path, now)
    except (ConfigError, sqlite3.Error) as error:
        Console(stderr=True).print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error

    Console().print(_summary_message(retention_result))


def _prune_from_options(
    configuration_path: Path,
    database_path: Path | None,
    now: str | None,
) -> LlmAuditRetentionResult:
    with connect_database(
        _database_path_from_options(configuration_path, database_path),
    ) as database_connection:
        return prune_llm_audit_logs(database_connection, _cleanup_timestamp(now))


def _database_path_from_options(configuration_path: Path, database_path: Path | None) -> Path:
    if database_path is not None:
        return database_path.expanduser()
    return load_database_path(configuration_path)


def _cleanup_timestamp(now: str | None) -> str:
    if now is None:
        return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    normalized_now = now.removesuffix("Z") + "+00:00" if now.endswith("Z") else now
    try:
        parsed_now = datetime.fromisoformat(normalized_now)
    except ValueError as error:
        raise ConfigError("--now must be an ISO timestamp like 2026-10-24T09:00:00Z") from error
    if parsed_now.tzinfo is None:
        raise ConfigError("--now must include a timezone like 2026-10-24T09:00:00Z")
    return parsed_now.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _summary_message(retention_result: LlmAuditRetentionResult) -> str:
    return (
        f"Deleted {retention_result.deleted_count} restricted LLM audit logs "
        f"expired before {retention_result.cutoff_at}."
    )
