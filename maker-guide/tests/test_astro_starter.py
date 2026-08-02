"""Integration coverage for the packaged Astro starter."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from importlib import resources
from pathlib import Path

import pytest


@pytest.mark.integration
def test_astro_starter_installs_dependencies_and_builds(temporary_path: Path) -> None:
    """The packaged learner starter installs and renders a learner page."""
    learner_home = temporary_path / "alice"
    learner_home.mkdir()
    destination = learner_home / "src"
    starter = resources.files("maker_guide.astro_starter").joinpath("template")
    with resources.as_file(starter) as starter_path:
        shutil.copytree(starter_path, destination)
    (destination / "pages" / "index.md").write_text("# Alice's page\n", encoding="utf-8")
    environment = {
        environment_name: value
        for environment_name, value in os.environ.items()
        if not environment_name.startswith("GIT_")
    } | {"HOME": str(learner_home), "ASTRO_TELEMETRY_DISABLED": "1"}
    npm_executable = shutil.which("npm")
    if npm_executable is None:
        raise RuntimeError("npm is required to build the learner website")

    subprocess.run(
        (npm_executable, "ci"),
        check=True,
        cwd=destination,
        env=environment,
    )
    subprocess.run(
        (str(Path(sys.executable).parent / "maker-guide-build-personal-website"),),
        check=True,
        cwd=learner_home,
        env=environment,
    )

    output_content = (learner_home / "public_html" / "index.html").read_text(encoding="utf-8")
    assert "Alice" in output_content
    assert "A Linux site under construction" not in output_content
