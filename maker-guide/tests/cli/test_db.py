"""Tests for database migration wrapper command."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

from maker_guide.cli.db import AlembicRunner, run
from tests.conftest import PACKAGE_ROOT

if TYPE_CHECKING:
    import pytest


@dataclass(frozen=True, kw_only=True, slots=True)
class AlembicCall:
    """Captured Alembic runner call."""

    arguments: tuple[str, ...]
    database_path: str | None
    working_directory: Path


def test_db_wrapper_uses_configured_database_path_without_irc_secret(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The wrapper reads only database config before delegating to Alembic."""
    monkeypatch.delenv("MAKER_GUIDE_IRC_PASSWORD", raising=False)
    database_path = temporary_path / "state.db"
    alembic_calls: list[AlembicCall] = []

    assert (
        run(
            ["--config", str(_write_database_config(temporary_path, database_path)), "current"],
            runner=_recording_runner(alembic_calls),
        )
        == 0
    )
    assert alembic_calls == [
        AlembicCall(
            arguments=("current",),
            database_path=str(database_path),
            working_directory=PACKAGE_ROOT,
        ),
    ]


def test_db_wrapper_database_argument_overrides_config(temporary_path: Path) -> None:
    """The operator can override the configured database path explicitly."""
    configured_database_path = temporary_path / "configured.db"
    override_database_path = temporary_path / "override.db"
    alembic_calls: list[AlembicCall] = []

    assert (
        run(
            [
                "--config",
                str(_write_database_config(temporary_path, configured_database_path)),
                "--database",
                str(override_database_path),
                "upgrade",
                "head",
            ],
            runner=_recording_runner(alembic_calls),
        )
        == 0
    )
    assert alembic_calls[0].database_path == str(override_database_path)


def test_db_wrapper_history_does_not_require_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Alembic history can run without a database path."""
    monkeypatch.delenv("MAKER_GUIDE_DB_PATH", raising=False)
    alembic_calls: list[AlembicCall] = []

    assert run(["history"], runner=_recording_runner(alembic_calls)) == 0
    assert alembic_calls == [
        AlembicCall(arguments=("history",), database_path=None, working_directory=PACKAGE_ROOT),
    ]


def test_db_wrapper_ignores_caller_alembic_project(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The wrapper always uses packaged migrations, not caller-owned Alembic files."""
    malicious_project = temporary_path / "malicious"
    malicious_project.mkdir()
    (malicious_project / "alembic.ini").write_text(
        "[alembic]\nscript_location = malicious_migrations\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(malicious_project)
    alembic_calls: list[AlembicCall] = []

    assert run(["history"], runner=_recording_runner(alembic_calls)) == 0
    assert alembic_calls == [
        AlembicCall(arguments=("history",), database_path=None, working_directory=PACKAGE_ROOT),
    ]


def test_db_wrapper_runs_real_migration(temporary_path: Path) -> None:
    """The wrapper can run Alembic against the configured SQLite path."""
    database_path = temporary_path / "state.db"

    assert (
        run(
            [
                "--config",
                str(_write_database_config(temporary_path, database_path)),
                "upgrade",
                "head",
            ]
        )
        == 0
    )
    with sqlite3.connect(database_path) as database_connection:
        table_name_rows = cast(
            "list[tuple[str]]",
            database_connection.execute(
                "select name from sqlite_master where type = 'table'",
            ).fetchall(),
        )

    assert "learners" in {table_name for (table_name,) in table_name_rows}


def _recording_runner(alembic_calls: list[AlembicCall]) -> AlembicRunner:
    def runner(
        arguments: Sequence[str],
        environment: Mapping[str, str],
        working_directory: Path,
    ) -> int:
        alembic_calls.append(
            AlembicCall(
                arguments=tuple(arguments),
                database_path=environment.get("MAKER_GUIDE_DB_PATH"),
                working_directory=working_directory,
            ),
        )
        return 0

    return runner


def _write_database_config(temporary_path: Path, database_path: Path) -> Path:
    configuration_path = temporary_path / "config.toml"
    configuration_path.write_text(
        f"""
        [database]
        path = "{database_path}"

        [irc.sasl]
        password_env = "MAKER_GUIDE_IRC_PASSWORD"
        """,
        encoding="utf-8",
    )
    return configuration_path
