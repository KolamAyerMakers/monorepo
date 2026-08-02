"""Database migration command wrapper."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, cast

import typer
from alembic.config import main as alembic_main
from rich.console import Console

from maker_guide.config import DEFAULT_CONFIG_PATH, ConfigError, load_database_path

AlembicRunner = Callable[[Sequence[str], Mapping[str, str], Path], int]

_DATABASE_OPTIONAL_COMMANDS = frozenset({"history"})
_PASSTHROUGH_CONTEXT_SETTINGS = {
    "allow_extra_args": True,
    "allow_interspersed_args": False,
    "ignore_unknown_options": True,
}
app = typer.Typer(
    add_completion=False,
    help="Run maker-guide database migrations.",
    pretty_exceptions_enable=False,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class DatabaseCommandDependencies:
    """Dependencies injected into the database command."""

    alembic_runner: AlembicRunner | None = None
    """Runner used instead of launching Alembic."""


def main() -> None:
    """Run the database migration wrapper."""
    app()


def run(
    arguments: Sequence[str] | None = None,
    runner: AlembicRunner | None = None,
) -> int:
    """Run the Typer app with injectable Alembic execution."""
    result = cast(
        "object",
        app(
            args=list(arguments) if arguments is not None else None,
            standalone_mode=False,
            obj=DatabaseCommandDependencies(alembic_runner=runner),
        ),
    )
    if isinstance(result, int):
        return result
    return 0


@app.command(context_settings=_PASSTHROUGH_CONTEXT_SETTINGS)
def migrate(
    context: typer.Context,
    configuration_path: Annotated[
        Path,
        typer.Option("--config", help="Path to the daemon TOML configuration."),
    ] = DEFAULT_CONFIG_PATH,
    database_path: Annotated[
        Path | None,
        typer.Option("--database", help="Override the configured SQLite database path."),
    ] = None,
) -> None:
    """Run Alembic with the configured database path."""
    alembic_arguments = tuple(context.args)
    if not alembic_arguments:
        Console(stderr=True).print("[red]Alembic command is required.[/red]")
        raise typer.Exit(2)

    raise typer.Exit(
        _run_migration(
            alembic_arguments,
            configuration_path,
            database_path,
            _runner_from_context(context),
        ),
    )


def _run_migration(
    alembic_arguments: Sequence[str],
    configuration_path: Path,
    database_path: Path | None,
    runner: AlembicRunner | None,
) -> int:
    """Run Alembic with explicit command options."""
    environment = os.environ.copy()
    resolved_database_path = _database_path_from_options(
        configuration_path,
        database_path,
        alembic_arguments,
    )
    if resolved_database_path is not None:
        environment["MAKER_GUIDE_DB_PATH"] = str(resolved_database_path)

    return (runner or _run_alembic)(
        alembic_arguments,
        environment,
        _alembic_working_directory(),
    )


def _database_path_from_options(
    configuration_path: Path,
    database_path: Path | None,
    alembic_arguments: Sequence[str],
) -> Path | None:
    if database_path is not None:
        return database_path.expanduser()
    if _requires_database_path(alembic_arguments):
        return load_database_path(configuration_path)
    return None


def _requires_database_path(alembic_arguments: Sequence[str]) -> bool:
    return alembic_arguments[0] not in _DATABASE_OPTIONAL_COMMANDS


def _run_alembic(
    alembic_arguments: Sequence[str],
    environment: Mapping[str, str],
    working_directory: Path,
) -> int:
    original_environment = os.environ.copy()
    original_working_directory = Path.cwd()
    logging_state = _capture_logging_state()
    os.environ.clear()
    os.environ.update(environment)
    os.chdir(working_directory)
    try:
        alembic_main(argv=list(alembic_arguments))
    except SystemExit as system_exit:
        return _system_exit_code(system_exit)
    finally:
        os.chdir(original_working_directory)
        os.environ.clear()
        os.environ.update(original_environment)
        _restore_logging_state(logging_state)
    return 0


def _system_exit_code(system_exit: SystemExit) -> int:
    if system_exit.code is None:
        return 0
    if isinstance(system_exit.code, int):
        return system_exit.code
    Console(stderr=True).out(str(system_exit.code))
    return 1


def _capture_logging_state() -> dict[str, object]:
    root_logger = logging.getLogger()
    logger_states: dict[str, tuple[bool, int, bool, list[logging.Handler]]] = {}
    for logger_name, logger_object in logging.Logger.manager.loggerDict.items():
        if isinstance(logger_object, logging.Logger):
            logger_states[logger_name] = (
                logger_object.disabled,
                logger_object.level,
                logger_object.propagate,
                list(logger_object.handlers),
            )
    return {
        "disable": logging.Logger.manager.disable,
        "root": (root_logger.disabled, root_logger.level, list(root_logger.handlers)),
        "loggers": logger_states,
    }


def _restore_logging_state(logging_state: dict[str, object]) -> None:
    logging.disable(cast("int", logging_state["disable"]))
    root_disabled, root_level, root_handlers = cast(
        "tuple[bool, int, list[logging.Handler]]",
        logging_state["root"],
    )
    root_logger = logging.getLogger()
    root_logger.disabled = root_disabled
    root_logger.setLevel(root_level)
    root_logger.handlers = root_handlers
    logger_states = cast(
        "dict[str, tuple[bool, int, bool, list[logging.Handler]]]",
        logging_state["loggers"],
    )
    for logger_name, logger_state in logger_states.items():
        logger_object = logging.getLogger(logger_name)
        logger_object.disabled = logger_state[0]
        logger_object.setLevel(logger_state[1])
        logger_object.propagate = logger_state[2]
        logger_object.handlers = logger_state[3]


def _runner_from_context(context: typer.Context) -> AlembicRunner | None:
    context_object = cast("object", context.obj)
    if isinstance(context_object, DatabaseCommandDependencies):
        return context_object.alembic_runner
    return None


def _alembic_working_directory() -> Path:
    package_directory = Path(__file__).resolve().parents[1]
    if (package_directory / "alembic.ini").is_file():
        return package_directory
    raise ConfigError("packaged alembic.ini is missing")
