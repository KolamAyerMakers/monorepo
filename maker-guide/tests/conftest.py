"""Shared test fixtures."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from maker_guide.projections import makers as makers_projection

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "src" / "maker_guide"


@pytest.fixture
def temporary_path(tmp_path: Path) -> Path:
    """Expose pytest's temporary path fixture under a non-abbreviated name."""
    return tmp_path


@pytest.fixture(autouse=True)
def skip_physical_fsync(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep durability tests semantic without forcing real disk flushes."""

    def no_fsync(file_descriptor: int) -> None:
        del file_descriptor

    monkeypatch.setattr(makers_projection.os, "fsync", no_fsync)


@pytest.fixture
def migrated_database_path(
    temporary_path: Path,
    migrated_database_template_path: Path,
) -> Path:
    """Create a temporary SQLite database from the migrated template."""
    database_path = temporary_path / "state.db"
    shutil.copy2(migrated_database_template_path, database_path)
    return database_path


@pytest.fixture(scope="session")
def migrated_database_template_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create one migrated SQLite template for tests that only need the schema."""
    database_path = tmp_path_factory.mktemp("database-template") / "state.db"
    run_alembic(database_path, "upgrade", "head")
    return database_path


def run_alembic(database_path: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run the Alembic CLI against a SQLite database path."""
    environment = os.environ.copy()
    environment["MAKER_GUIDE_DB_PATH"] = str(database_path)
    completed_process = subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        check=False,
        cwd=PACKAGE_ROOT,
        env=environment,
        capture_output=True,
        text=True,
    )
    if completed_process.returncode != 0:
        raise AssertionError(
            "\n".join(
                (
                    f"alembic {' '.join(arguments)} failed",
                    "stdout:",
                    completed_process.stdout,
                    "stderr:",
                    completed_process.stderr,
                ),
            ),
        )
    return completed_process
