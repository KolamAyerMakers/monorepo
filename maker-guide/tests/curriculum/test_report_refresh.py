"""Protect the published report from failed unattended collection."""

from __future__ import annotations

import os
import subprocess
from importlib.resources import files
from pathlib import Path

import pytest


@pytest.mark.parametrize("failed_command", [None, "hostname", "cut", "mv"])
def test_report_refresh_preserves_last_valid_report_on_failure(
    temporary_path: Path, failed_command: str | None
) -> None:
    """A failed collection or publication command preserves the last valid report."""
    report_path = temporary_path / "src" / "pages" / "maker-report.md"
    report_path.parent.mkdir(parents=True)
    report_path.write_text("last valid report\n", encoding="utf-8")
    command_directory = temporary_path / "commands"
    command_directory.mkdir()
    if failed_command is not None:
        command_directory.joinpath(failed_command).write_text(
            "#!/bin/bash\nprintf 'collection or publication failed\\n' >&2\nexit 1\n",
            encoding="utf-8",
        )
        command_directory.joinpath(failed_command).chmod(0o755)

    completed_process = subprocess.run(
        [
            "/bin/bash",
            "-c",
            files("maker_guide.curriculum")
            .joinpath("content/lf2607/guides/resources/maker-report.sh")
            .read_text(encoding="utf-8"),
            "maker-report.sh",
            "Automatic Report",
        ],
        env=os.environ
        | {"HOME": str(temporary_path), "PATH": f"{command_directory}:{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    if failed_command is None:
        assert completed_process.returncode == 0, completed_process.stderr
        assert report_path.read_text(encoding="utf-8").startswith("# Automatic Report\n")
    else:
        assert completed_process.returncode != 0
        assert report_path.read_text(encoding="utf-8") == "last valid report\n"
    assert list(report_path.parent.glob(".maker-report.*")) == []
