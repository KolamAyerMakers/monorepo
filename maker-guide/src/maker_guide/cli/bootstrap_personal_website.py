"""Bootstrap and build the learner-owned Astro website project."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from importlib import resources
from pathlib import Path
from typing import cast

from rich.console import Console

from maker_guide.astro_shared.theme import copy_site_theme

_STARTER_MARKER = ".astro-starter-marker"
_INITIAL_COMMIT_MESSAGE = "chore: seed astro site"
_LEARNER_STYLESHEET = Path("app/styles/student.css")
_LEARNER_ASSET_DIRECTORY = Path("public/student")


def main(arguments: Sequence[str] | None = None) -> int:
    """Bootstrap a site once, then build it on every later invocation."""
    parser = argparse.ArgumentParser(description="Bootstrap and build a learner Astro website.")
    _ = parser.add_argument("--destination", type=Path, default=Path.home() / "src")
    _ = parser.add_argument(
        "--sync", action="store_true", help="Refresh class-managed site files only."
    )
    parsed_arguments = parser.parse_args(arguments)
    destination = cast("Path", parsed_arguments.destination).expanduser()
    sync_only = cast("bool", parsed_arguments.sync)
    try:
        if destination.exists():
            if not (destination / _STARTER_MARKER).is_file():
                raise _existing_project_error(destination)
            dependencies_changed = _copy_managed_assets(destination)
            if dependencies_changed:
                _run(("npm", "ci"), destination)
        else:
            if sync_only:
                raise _missing_project_error(destination)
            _bootstrap(destination)
        if not sync_only:
            _run(("node", "scripts/build.mjs"), destination)
    except (FileExistsError, FileNotFoundError, subprocess.CalledProcessError) as error:
        Console(stderr=True).print(_error_message(error))
        return 1
    return 0


def _copy_starter(destination: Path) -> None:
    starter = resources.files("maker_guide.astro_starter").joinpath("template")
    with resources.as_file(starter) as starter_path:
        shutil.copytree(starter_path, destination, dirs_exist_ok=True)
    _copy_managed_assets(destination)


def _copy_managed_assets(destination: Path) -> bool:
    """Refresh class-owned files without touching learner pages or extensions."""
    package_lock = destination / "package-lock.json"
    previous_lock = package_lock.read_bytes() if package_lock.is_file() else None
    starter = resources.files("maker_guide.astro_starter").joinpath("template")
    with resources.as_file(starter) as starter_path:

        def ignore(directory: str, entries: list[str]) -> set[str]:
            ignored = shutil.ignore_patterns(".gitignore")(directory, entries)
            if Path(directory) == starter_path:
                ignored.add("pages")
            return ignored

        shutil.copytree(
            starter_path,
            destination,
            dirs_exist_ok=True,
            ignore=ignore,
        )
    copy_site_theme(destination / "app" / "styles" / "site.css")
    _ensure_learner_extensions(destination)
    return previous_lock != package_lock.read_bytes()


def _ensure_learner_extensions(destination: Path) -> None:
    """Create learner extension points once, preserving later changes."""
    learner_stylesheet = destination / _LEARNER_STYLESHEET
    learner_stylesheet.parent.mkdir(parents=True, exist_ok=True)
    learner_stylesheet.touch(exist_ok=True)
    (destination / _LEARNER_ASSET_DIRECTORY).mkdir(parents=True, exist_ok=True)


def _bootstrap(destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_directory = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent)
    )
    try:
        _copy_starter(temporary_directory)
        _run(("npm", "ci"), temporary_directory)
        _run(("git", "init", "--initial-branch=main"), temporary_directory)
        _run(("git", "add", "--all"), temporary_directory)
        _run(("git", "commit", "-m", _INITIAL_COMMIT_MESSAGE), temporary_directory)
        temporary_directory.replace(destination)
    except Exception:
        shutil.rmtree(temporary_directory, ignore_errors=True)
        raise


def _existing_project_error(destination: Path) -> FileExistsError:
    return FileExistsError(f"{destination} already exists and is not a Kolam Astro site")


def _missing_project_error(destination: Path) -> FileNotFoundError:
    return FileNotFoundError(f"{destination} does not exist; run build-website first")


def _run(command: tuple[str, ...], destination: Path) -> None:
    _ = subprocess.run(command, check=True, cwd=destination)  # noqa: S603 - fixed tool commands.


def _error_message(
    error: FileExistsError | FileNotFoundError | subprocess.CalledProcessError,
) -> str:
    if isinstance(error, OSError):
        return str(error)
    command = cast("Sequence[object]", error.cmd)
    return f"{' '.join(str(part) for part in command)} failed with status {error.returncode}"
