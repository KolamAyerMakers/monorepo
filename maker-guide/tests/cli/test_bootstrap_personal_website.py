"""Tests for the learner-owned Astro website bootstrap command."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from maker_guide.cli import bootstrap_personal_website

if TYPE_CHECKING:
    import pytest


def test_bootstrap_copies_starter_installs_dependencies_and_commits(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A new site receives the pinned starter and one initial source commit."""
    commands: list[tuple[Sequence[str], Path]] = []
    destination = temporary_path / "src"

    def run(
        command: Sequence[str], **keyword_arguments: object
    ) -> subprocess.CompletedProcess[str]:
        working_directory = keyword_arguments["cwd"]
        assert isinstance(working_directory, Path)
        commands.append((command, working_directory))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", run)

    assert bootstrap_personal_website.main(["--destination", str(destination)]) == 0
    assert (destination / "package.json").is_file()
    assert (destination / "package-lock.json").is_file()
    assert (destination / "pages" / "index.md").is_file()
    assert "base: `/~${userInfo().username}/`," in (destination / "astro.config.mjs").read_text(
        encoding="utf-8"
    )
    assert "brand-logo-dark" in (destination / "app" / "layouts" / "SiteLayout.astro").read_text(
        encoding="utf-8"
    )
    assert (destination / "app" / "pages" / "points-ledger.astro").is_file()
    assert (destination / "app" / "pages" / "[...slug].astro").is_file()
    assert (destination / "app" / "styles" / "student.css").is_file()
    assert (destination / "public" / "kolam-ayer-makers.png").is_file()
    assert (destination / "public" / "kolam-ayer-makers-dark.png").is_file()
    assert (destination / "public" / "student").is_dir()
    theme_content = (destination / "app" / "styles" / "site.css").read_text(encoding="utf-8")
    assert ".site-shell" in theme_content
    assert "prefers-color-scheme" in theme_content
    assert [command for command, _working_directory in commands] == [
        ("npm", "ci"),
        ("git", "init", "--initial-branch=main"),
        ("git", "add", "--all"),
        ("git", "commit", "-m", "chore: seed astro site"),
        ("node", "scripts/build.mjs"),
    ]
    assert all(working_directory != destination for _, working_directory in commands[:-1])
    assert commands[-1][1] == destination


def test_bootstrap_refuses_existing_project(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The bootstrap refuses projects that were not created by the class."""
    destination = temporary_path / "src"
    destination.mkdir()
    was_called = False

    def run(
        command: Sequence[str], **_keyword_arguments: object
    ) -> subprocess.CompletedProcess[str]:
        nonlocal was_called
        was_called = True
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", run)

    assert bootstrap_personal_website.main(["--destination", str(destination)]) == 1
    assert "already" in capsys.readouterr().err
    assert was_called is False


def test_bootstrap_rebuilds_seeded_project_and_preserves_learner_extensions(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Later builds refresh class files without overwriting learner extensions."""
    destination = temporary_path / "src"
    destination.mkdir()
    (destination / ".astro-starter-marker").write_text("1\n", encoding="utf-8")
    learner_page = destination / "pages" / "index.md"
    learner_page.parent.mkdir()
    learner_page.write_text("# Learner page\n", encoding="utf-8")
    learner_stylesheet = destination / "app" / "styles" / "student.css"
    learner_stylesheet.parent.mkdir(parents=True)
    learner_stylesheet.write_text("body { color: tomato; }\n", encoding="utf-8")
    learner_asset = destination / "public" / "student" / "portrait.txt"
    learner_asset.parent.mkdir(parents=True)
    learner_asset.write_text("learner asset\n", encoding="utf-8")
    (destination / "astro.config.mjs").write_text("learner change\n", encoding="utf-8")
    commands: list[Sequence[str]] = []

    def run(
        command: Sequence[str], **_keyword_arguments: object
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", run)

    assert bootstrap_personal_website.main(["--destination", str(destination)]) == 0
    assert commands == [("npm", "ci"), ("node", "scripts/build.mjs")]
    assert "prefers-color-scheme" in (destination / "app" / "styles" / "site.css").read_text(
        encoding="utf-8"
    )
    assert "base: `/~${userInfo().username}/`," in (destination / "astro.config.mjs").read_text(
        encoding="utf-8"
    )
    assert "brand-logo-dark" in (destination / "app" / "layouts" / "SiteLayout.astro").read_text(
        encoding="utf-8"
    )
    assert (destination / "app" / "pages" / "points-ledger.astro").is_file()
    assert (destination / "public" / "kolam-ayer-makers.png").is_file()
    assert (destination / "public" / "kolam-ayer-makers-dark.png").is_file()
    assert learner_page.read_text(encoding="utf-8") == "# Learner page\n"
    assert learner_stylesheet.read_text(encoding="utf-8") == "body { color: tomato; }\n"
    assert learner_asset.read_text(encoding="utf-8") == "learner asset\n"


def test_bootstrap_reinstalls_dependencies_only_after_lockfile_update(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unchanged managed dependencies do not trigger another npm install."""
    destination = temporary_path / "src"
    destination.mkdir()
    (destination / ".astro-starter-marker").write_text("1\n", encoding="utf-8")
    starter_lockfile = (
        resources.files("maker_guide.astro_starter")
        .joinpath("template", "package-lock.json")
        .read_bytes()
    )
    (destination / "package-lock.json").write_bytes(starter_lockfile)
    commands: list[Sequence[str]] = []

    def run(
        command: Sequence[str], **_keyword_arguments: object
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", run)

    assert bootstrap_personal_website.main(["--destination", str(destination)]) == 0
    assert commands == [("node", "scripts/build.mjs")]


def test_sync_refreshes_class_files_without_running_the_build(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A direct npm build can update its framework before invoking Astro."""
    destination = temporary_path / "src"
    destination.mkdir()
    (destination / ".astro-starter-marker").write_text("1\n", encoding="utf-8")
    (destination / "package-lock.json").write_bytes(
        resources.files("maker_guide.astro_starter")
        .joinpath("template", "package-lock.json")
        .read_bytes()
    )
    commands: list[Sequence[str]] = []

    def run(
        command: Sequence[str], **_keyword_arguments: object
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", run)

    assert bootstrap_personal_website.main(["--destination", str(destination), "--sync"]) == 0
    assert commands == []
    assert "maker-guide-build-personal-website --sync" in (destination / "package.json").read_text(
        encoding="utf-8"
    )


def test_sync_requires_an_existing_class_site(
    temporary_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The npm pre-build hook cannot bootstrap a missing project."""
    destination = temporary_path / "src"

    assert bootstrap_personal_website.main(["--destination", str(destination), "--sync"]) == 1
    assert "run build-website first" in capsys.readouterr().err


def test_bootstrap_reports_failed_tool(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A failed setup tool stops the bootstrap with an actionable error."""
    destination = temporary_path / "src"

    def run(
        command: Sequence[str], **_keyword_arguments: object
    ) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(subprocess, "run", run)

    assert bootstrap_personal_website.main(["--destination", str(destination)]) == 1
    assert "npm ci failed with status 1" in capsys.readouterr().err
    assert destination.exists() is False
