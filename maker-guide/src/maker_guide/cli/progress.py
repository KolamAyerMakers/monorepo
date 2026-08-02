"""Learner progress reporting command."""

from __future__ import annotations

import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Annotated, cast
from zoneinfo import ZoneInfo

import typer
from rich.console import Console
from rich.table import Table

from maker_guide.config import DEFAULT_CONFIG_PATH, ConfigError, load_database_path
from maker_guide.curriculum.catalogs import DEFAULT_COURSE_ID, catalog_by_course_id
from maker_guide.curriculum.models import Course, CourseCatalog, Session
from maker_guide.curriculum.tiers import current_tier_id
from maker_guide.progress.models import (
    CourseReleaseInput,
    CourseReleaseResult,
)
from maker_guide.progress.service import (
    ProgressServiceError,
    release_course,
)
from maker_guide.repositories.cohort_membership import list_memberships
from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.maker_projection import (
    MakerCompletedQuest,
    MakerLearnerState,
    list_maker_completed_quests,
    list_maker_learner_states,
)
from maker_guide.repositories.quest_completion import list_completed_quest_ids
from maker_guide.repositories.session_objective_completion import list_completed_objective_ids

_BUILD_DOCS_SERVICE = "maker-guide-build-docs.service"

app = typer.Typer(
    add_completion=False,
    help="Inspect learner progress.",
    no_args_is_help=False,
    pretty_exceptions_enable=False,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class _ProgressOptions:
    configuration_path: Path
    database_path: Path | None
    course_id: str


def run(arguments: list[str] | None = None) -> int:
    """Run the Typer app for tests."""
    result = cast(
        "object",
        app(
            args=arguments,
            standalone_mode=False,
        ),
    )
    if isinstance(result, int):
        return result
    return 0


def main() -> None:
    """Run the progress reporting command."""
    app()


@app.callback(invoke_without_command=True)
def progress(
    context: typer.Context,
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
        typer.Option("--course-id", help="Course id to inspect."),
    ] = DEFAULT_COURSE_ID,
) -> None:
    """Show the learner progress table by default."""
    if context.invoked_subcommand is not None:
        return
    _print_progress_table(
        _ProgressOptions(
            configuration_path=configuration_path,
            database_path=database_path,
            course_id=course_id,
        )
    )


@app.command("list")
def list_progress(
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
        typer.Option("--course-id", help="Course id to inspect."),
    ] = DEFAULT_COURSE_ID,
) -> None:
    """Show all learners ranked by score and completion progress."""
    _print_progress_table(
        _ProgressOptions(
            configuration_path=configuration_path,
            database_path=database_path,
            course_id=course_id,
        )
    )


@app.command()
def show(
    handle: Annotated[str, typer.Argument(help="Learner handle to inspect.")],
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
        typer.Option("--course-id", help="Course id to inspect."),
    ] = DEFAULT_COURSE_ID,
) -> None:
    """Show one learner's progress and completed quests."""
    _print_learner_progress(
        handle,
        _ProgressOptions(
            configuration_path=configuration_path,
            database_path=database_path,
            course_id=course_id,
        ),
    )


@app.command()
def release(
    session_reached: Annotated[str, typer.Argument(help="Session id to release.")],
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
        typer.Option("--course-id", help="Course id to advance."),
    ] = DEFAULT_COURSE_ID,
    source: Annotated[str, typer.Option("--source", help="Audit source label.")] = "teacher",
) -> None:
    """Release a session to every learner in a course."""
    try:
        result = _release_course(
            _ProgressOptions(
                configuration_path=configuration_path,
                database_path=database_path,
                course_id=course_id,
            ),
            session_reached,
            source,
        )
    except (
        ConfigError,
        OSError,
        ProgressServiceError,
        sqlite3.Error,
        subprocess.CalledProcessError,
    ) as error:
        Console(stderr=True).print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error

    Console().print(
        f"released {result.course_release.session_reached}"
        if result.changed
        else f"already released {result.course_release.session_reached}",
    )


@app.command("live")
def live_summary(
    session_id: Annotated[
        str | None,
        typer.Argument(
            help="Session id to summarize. Defaults to the current dated class session.",
        ),
    ] = None,
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
        typer.Option("--course-id", help="Course id to inspect."),
    ] = DEFAULT_COURSE_ID,
) -> None:
    """Show durable objective and quest progress for one session."""
    try:
        _print_live_summary(
            _ProgressOptions(
                configuration_path=configuration_path,
                database_path=database_path,
                course_id=course_id,
            ),
            session_id,
        )
    except (ConfigError, ProgressServiceError, sqlite3.Error) as error:
        Console(stderr=True).print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error


def _print_progress_table(options: _ProgressOptions) -> None:
    try:
        catalog, learner_states = _learner_states(options)
    except (ConfigError, sqlite3.Error) as error:
        Console(stderr=True).print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error

    student_states = [
        learner_state for learner_state in learner_states if learner_state.rank_eligible
    ]
    non_student_states = [
        learner_state for learner_state in learner_states if not learner_state.rank_eligible
    ]
    course_release = learner_states[0].session_reached if learner_states else None
    _print_progress_table_for_states(
        catalog,
        student_states,
        course_release,
        title="Student Progress",
        ranked=True,
    )
    _print_progress_table_for_states(
        catalog,
        non_student_states,
        course_release,
        title="Non-student Progress",
        ranked=False,
    )


def _print_progress_table_for_states(
    catalog: CourseCatalog,
    learner_states: list[MakerLearnerState],
    course_release: str | None,
    *,
    title: str,
    ranked: bool,
) -> None:
    table = Table(
        title=f"{title} ({catalog.course.id}, course release: {course_release or 'none'})",
    )
    if ranked:
        table.add_column("Rank", justify="right", no_wrap=True)
    table.add_column("Handle", no_wrap=True)
    table.add_column("Score", justify="right", no_wrap=True)
    table.add_column("Tier", no_wrap=True)
    table.add_column("Quests", justify="right", no_wrap=True)
    table.add_column("Last score", no_wrap=True)
    for rank_position, learner_state in enumerate(_ranked_learner_states(learner_states), start=1):
        row = (
            learner_state.handle,
            str(learner_state.score_total),
            current_tier_id(catalog, learner_state.score_total) or "none",
            str(learner_state.completed_quest_count),
            learner_state.last_score_at or "never",
        )
        if ranked:
            table.add_row(str(rank_position), *row)
        else:
            table.add_row(*row)
    Console().print(table)


def _print_learner_progress(handle: str, options: _ProgressOptions) -> None:
    try:
        catalog, learner_states, completed_quests = _learner_progress_data(options)
    except (ConfigError, sqlite3.Error) as error:
        Console(stderr=True).print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error
    learner_state = next(
        (state for state in learner_states if state.handle == handle),
        None,
    )
    if learner_state is None:
        Console(stderr=True).print(f"[red]Unknown learner: {handle}[/red]")
        raise typer.Exit(2)

    summary = Table(title=f"{handle} Progress ({catalog.course.id})")
    summary.add_column("Metric", no_wrap=True)
    summary.add_column("Value")
    summary.add_row("Course release", learner_state.session_reached or "none")
    summary.add_row("Score", str(learner_state.score_total))
    summary.add_row("Tier", current_tier_id(catalog, learner_state.score_total) or "none")
    summary.add_row("Completed quests", str(learner_state.completed_quest_count))
    summary.add_row("Last score", learner_state.last_score_at or "none")

    completed_quest_by_id = {
        completed_quest.quest_id: completed_quest
        for completed_quest in completed_quests
        if completed_quest.handle == handle
    }
    quest_table = Table(title="Quest Progress")
    quest_table.add_column("Status", no_wrap=True)
    quest_table.add_column("Quest", no_wrap=True)
    quest_table.add_column("Step", overflow="fold")
    available_quests = (
        catalog.quests_available_through(learner_state.session_reached)
        if learner_state.session_reached is not None
        else ()
    )
    for quest in available_quests:
        completed_quest = completed_quest_by_id.get(quest.id)
        for step_position, step in enumerate(quest.autonomy_checklist, start=1):
            quest_table.add_row(
                ("done" if completed_quest is not None else "todo") if step_position == 1 else "",
                quest.id if step_position == 1 else "",
                f"{_progress_marker(completed_quest is not None)} {step}",
            )
    Console().print(summary)
    Console().print(quest_table)


def _print_live_summary(options: _ProgressOptions, session_id: str | None) -> None:
    catalog = _catalog_from_options(options)
    with connect_database(_database_path_from_options(options)) as database_connection:
        memberships = list_memberships(database_connection, catalog.course.id)
        session = _session_from_catalog(
            catalog,
            session_id or _current_session_id(catalog.course, _course_today(catalog.course)),
        )
        quests = catalog.quests_available_after(session.id)
        table = Table(title=f"Session Progress {session.id} ({catalog.course.id})")
        table.add_column("Handle", no_wrap=True)
        for objective in session.objectives:
            table.add_column(objective.id, justify="center")
        for quest in quests:
            table.add_column(quest.id, justify="center")
        for membership in memberships:
            completed_objective_ids = list_completed_objective_ids(
                database_connection,
                membership.handle,
                catalog.course.id,
                session.id,
            )
            completed_quest_ids = list_completed_quest_ids(
                database_connection,
                membership.handle,
                catalog.course.id,
            )
            table.add_row(
                membership.handle,
                *(
                    "yes" if objective.id in completed_objective_ids else "-"
                    for objective in session.objectives
                ),
                *("yes" if quest.id in completed_quest_ids else "-" for quest in quests),
            )
    console = Console()
    console.print(table)
    if session.objectives:
        console.print("Objectives: " + ", ".join(objective.id for objective in session.objectives))
    if quests:
        console.print("Quests: " + ", ".join(quest.id for quest in quests))


def _current_session_id(course: Course, today: date) -> str:
    for session in reversed(course.sessions):
        if session.date <= today:
            return session.id
    return course.sessions[0].id


def _course_today(course: Course) -> date:
    return datetime.now(ZoneInfo(course.timezone)).date()


def _progress_marker(completed: bool) -> str:
    return "[x]" if completed else "[ ]"


def _release_course(
    options: _ProgressOptions,
    session_reached: str,
    source: str,
) -> CourseReleaseResult:
    catalog = catalog_by_course_id(options.course_id)
    if catalog is None:
        raise ConfigError(f"unknown course id: {options.course_id}")

    with connect_database(_database_path_from_options(options)) as database_connection:
        release_result = release_course(
            database_connection,
            catalog,
            CourseReleaseInput(
                session_reached=_session_from_catalog(catalog, session_reached).id,
                updated_at=_utc_timestamp(),
                source=source,
            ),
        )
    if release_result.changed:
        _start_docs_build()
    return release_result


def _start_docs_build() -> None:
    """Request publication from the Salt-managed documentation builder."""
    _ = subprocess.run(  # noqa: S603 - fixed Salt-managed service command.
        ("/usr/bin/sudo", "-n", "/usr/bin/systemctl", "start", _BUILD_DOCS_SERVICE),
        check=True,
    )


def _learner_states(
    options: _ProgressOptions,
) -> tuple[CourseCatalog, list[MakerLearnerState]]:
    catalog = _catalog_from_options(options)
    with connect_database(_database_path_from_options(options)) as database_connection:
        return catalog, list_maker_learner_states(database_connection, catalog.course.id)


def _learner_progress_data(
    options: _ProgressOptions,
) -> tuple[CourseCatalog, list[MakerLearnerState], list[MakerCompletedQuest]]:
    catalog, learner_states = _learner_states(options)
    with connect_database(_database_path_from_options(options)) as database_connection:
        return (
            catalog,
            learner_states,
            list_maker_completed_quests(database_connection, catalog.course.id),
        )


def _catalog_from_options(options: _ProgressOptions) -> CourseCatalog:
    catalog = catalog_by_course_id(options.course_id)
    if catalog is None:
        raise ConfigError(f"unknown course id: {options.course_id}")
    return catalog


def _session_from_catalog(catalog: CourseCatalog, session_id: str) -> Session:
    try:
        if session_id[:1].casefold() == "s" and session_id[1:].isdecimal():
            session_id = f"S{int(session_id[1:])}"
        return catalog.session(session_id)
    except KeyError as key_error:
        raise ProgressServiceError(f"unknown session: {session_id}") from key_error


def _database_path_from_options(options: _ProgressOptions) -> Path:
    if options.database_path is not None:
        return options.database_path.expanduser()
    return load_database_path(options.configuration_path)


def _utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ranked_learner_states(learner_states: list[MakerLearnerState]) -> list[MakerLearnerState]:
    return sorted(
        learner_states,
        key=lambda learner_state: (
            -learner_state.score_total,
            -learner_state.completed_quest_count,
            learner_state.last_score_at is None,
            learner_state.last_score_at or "",
            learner_state.handle,
        ),
    )
