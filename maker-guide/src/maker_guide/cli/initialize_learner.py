"""Initialize app state for a provisioned learner account."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, cast

import typer
from rich.console import Console

from maker_guide.config import DEFAULT_CONFIG_PATH, ConfigError, load_database_path
from maker_guide.curriculum.catalogs import DEFAULT_COURSE_ID, catalog_by_course_id
from maker_guide.enrollment.models import EnrollmentInput, EnrollmentServiceError
from maker_guide.enrollment.service import enroll
from maker_guide.identity.models import EnsureLearnerInput
from maker_guide.identity.policy import is_managed_uid
from maker_guide.identity.service import ensure_learner
from maker_guide.repositories.helpers import connect_database, transaction

app = typer.Typer(
    add_completion=False,
    help="Initialize maker-guide state for a newly provisioned learner.",
    pretty_exceptions_enable=False,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class InitializeLearnerOptions:
    """Resolved options for one learner initialization run."""

    handle: str
    configuration_path: Path
    database_path: Path | None
    course_id: str
    source: str
    joined_at: str
    uid: int
    enroll: bool
    rank_eligible: bool


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
def initialize(  # noqa: PLR0913 - Typer command options are declared as parameters.
    handle: Annotated[str, typer.Argument(help="Learner handle to initialize.")],
    *,
    configuration_path: Annotated[
        Path,
        typer.Option("--config", help="Path to the daemon TOML configuration."),
    ] = DEFAULT_CONFIG_PATH,
    database_path: Annotated[
        Path | None,
        typer.Option("--database", help="Override the configured SQLite database path."),
    ] = None,
    course_id: Annotated[
        str,
        typer.Option("--course-id", help="Course id to enroll."),
    ] = DEFAULT_COURSE_ID,
    source: Annotated[
        str,
        typer.Option("--source", help="Audit source label."),
    ] = "registration",
    joined_at: Annotated[
        str | None,
        typer.Option("--joined-at", help="Override join timestamp for tests."),
    ] = None,
    uid: Annotated[
        int,
        typer.Option("--uid", help="Provisioned POSIX uid."),
    ],
    enroll: Annotated[
        bool,
        typer.Option("--enroll/--no-enroll", help="Enroll the identity in the course."),
    ] = True,
    rank_eligible: Annotated[
        bool,
        typer.Option(
            "--rank-eligible/--not-rank-eligible",
            help="Include the learner in cohort rankings.",
        ),
    ] = True,
) -> None:
    """Ensure an identity exists and optionally enroll it in the default course."""
    try:
        result = _initialize_from_options(
            InitializeLearnerOptions(
                handle=handle,
                configuration_path=configuration_path,
                database_path=database_path,
                course_id=course_id,
                source=source,
                joined_at=joined_at or _utc_timestamp(),
                uid=uid,
                enroll=enroll,
                rank_eligible=rank_eligible,
            ),
        )
    except (ConfigError, EnrollmentServiceError, sqlite3.Error) as error:
        Console(stderr=True).print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error

    Console().print(result)


def _initialize_from_options(options: InitializeLearnerOptions) -> str:
    if not is_managed_uid(options.uid):
        raise EnrollmentServiceError(f"unsafe provisioned uid: {options.uid}")
    with (
        connect_database(
            _database_path_from_options(options.configuration_path, options.database_path),
        ) as connection,
        transaction(connection),
    ):
        learner_result = ensure_learner(
            connection,
            EnsureLearnerInput(
                handle=options.handle,
                joined_at=options.joined_at,
                source=options.source,
                uid=options.uid,
            ),
        )
        if not options.enroll:
            return f"learner {'created' if learner_result.created else 'exists'}: {options.handle}"

        selected_catalog = catalog_by_course_id(options.course_id)
        if selected_catalog is None:
            raise EnrollmentServiceError(f"unknown course id: {options.course_id}")
        enrollment_result = enroll(
            connection,
            EnrollmentInput(
                handle=options.handle,
                course_id=selected_catalog.course.id,
                joined_at=options.joined_at,
                source=options.source,
                rank_eligible=options.rank_eligible,
            ),
        )
    return "; ".join(
        (
            f"learner {'created' if learner_result.created else 'exists'}: {options.handle}",
            "enrollment {}: {}".format(
                "created" if enrollment_result.created else "exists",
                selected_catalog.course.id,
            ),
        ),
    )


def _database_path_from_options(configuration_path: Path, database_path: Path | None) -> Path:
    if database_path is not None:
        return database_path.expanduser()
    return load_database_path(configuration_path)


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
