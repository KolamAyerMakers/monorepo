"""Derived data synchronization command."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, cast

import typer
from rich.console import Console

from maker_guide.config import DEFAULT_CONFIG_PATH, ConfigError, load_database_path
from maker_guide.curriculum.catalogs import DEFAULT_COURSE_ID, catalog_by_course_id
from maker_guide.projections.makers import (
    MakersProjectionError,
    MakersProjectionOptions,
    MakersProjectionResult,
    sync_makers_projection,
)
from maker_guide.repositories.helpers import connect_database

app = typer.Typer(
    add_completion=False,
    help="Synchronize derived learner-visible data from SQLite.",
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
def sync(  # noqa: PLR0913
    *,
    configuration_path: Annotated[
        Path,
        typer.Option("--config", help="Path to the daemon TOML configuration."),
    ] = DEFAULT_CONFIG_PATH,
    database_path: Annotated[
        Path | None,
        typer.Option("--database", help="Override the configured SQLite database path."),
    ] = None,
    makers_root: Annotated[
        Path,
        typer.Option("--makers-root", help="Root directory for learner `/makers` files."),
    ] = Path("/makers"),
    documents_root: Annotated[
        Path,
        typer.Option("--documents-root", help="Root directory for learner curriculum docs."),
    ] = Path("/docs"),
    course_id: Annotated[
        str,
        typer.Option("--course-id", help="Course id to project."),
    ] = DEFAULT_COURSE_ID,
    process_outbox: Annotated[
        bool,
        typer.Option(
            "--process-outbox/--skip-outbox",
            help="Mark retryable projection outbox rows after a successful sync.",
        ),
    ] = True,
) -> None:
    """Regenerate `/makers` from SQLite."""
    try:
        projection_result = _sync_from_options(
            configuration_path,
            database_path,
            makers_root,
            documents_root,
            course_id,
            process_outbox,
        )
    except (ConfigError, MakersProjectionError, sqlite3.Error) as error:
        Console(stderr=True).print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error

    Console().print(_summary_message(projection_result))


def _sync_from_options(  # noqa: PLR0913
    configuration_path: Path,
    database_path: Path | None,
    makers_root: Path,
    documents_root: Path,
    course_id: str,
    process_outbox: bool,
) -> MakersProjectionResult:
    selected_catalog = catalog_by_course_id(course_id)
    if selected_catalog is None:
        raise MakersProjectionError(f"unknown course id: {course_id}")
    with connect_database(
        _database_path_from_options(configuration_path, database_path),
    ) as database_connection:
        return sync_makers_projection(
            database_connection,
            selected_catalog,
            MakersProjectionOptions(
                makers_root=makers_root.expanduser(),
                projected_at=_utc_timestamp(),
                documents_root=documents_root.expanduser(),
                process_outbox=process_outbox,
            ),
        )


def _database_path_from_options(configuration_path: Path, database_path: Path | None) -> Path:
    if database_path is not None:
        return database_path.expanduser()
    return load_database_path(configuration_path)


def _summary_message(projection_result: MakersProjectionResult) -> str:
    return "; ".join(
        (
            f"Projected {projection_result.learner_count} learners",
            f"processed {projection_result.processed_outbox_count} projection outbox rows.",
        ),
    )


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
