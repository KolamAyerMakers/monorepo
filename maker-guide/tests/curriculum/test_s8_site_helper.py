"""Protect the taught helper from serving an unrelated working directory."""

from __future__ import annotations

import re
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "document_path",
    [
        "sessions/S08/slides.md",
        "sessions/S08/self-study.md",
        "quests/write-site-helper-functions.md",
    ],
)
@pytest.mark.parametrize("public_directory_exists", [False, True])
def test_documented_helper_never_serves_callers_directory(
    temporary_path: Path,
    document_path: str,
    public_directory_exists: bool,
) -> None:
    """A missing public_html must not make Python expose the caller's files."""
    helper_match = re.search(
        r"^```bash\n(?P<helper>#!/bin/bash\n.*?)^```$",
        files("maker_guide.curriculum")
        .joinpath(f"content/lf2607/{document_path}")
        .read_text(encoding="utf-8"),
        re.MULTILINE | re.DOTALL,
    )
    assert helper_match is not None
    bash_path = shutil.which("bash")
    assert bash_path is not None
    home_directory = temporary_path / "learner home"
    home_directory.mkdir()
    public_directory = home_directory / "public_html"
    if public_directory_exists:
        public_directory.mkdir()
    unrelated_directory = temporary_path / "private working directory"
    unrelated_directory.mkdir()
    for command_name, command_body in (
        ("id", "printf '1234\\n'\n"),
        ("python3", 'printf \'%s\\n\' "$PWD" "$@"\n'),
    ):
        command_path = temporary_path / command_name
        command_path.write_text(f"#!{bash_path}\n{command_body}", encoding="utf-8")
        command_path.chmod(0o755)
    completed_process = subprocess.run(
        [bash_path, "-c", helper_match["helper"], "site.sh", "serve"],
        cwd=unrelated_directory,
        env={"HOME": str(home_directory), "PATH": str(temporary_path)},
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert completed_process.returncode == 0, completed_process.stderr
    output_lines = completed_process.stdout.splitlines()
    # ponytail: inspect Python's directory choice without opening a socket.
    assert (
        output_lines[output_lines.index("--directory") + 1]
        if "--directory" in output_lines
        else output_lines[0]
    ) == str(public_directory)
