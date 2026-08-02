"""Build the classroom documentation site from packaged curriculum content."""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import shlex
import shutil
import sqlite3
import subprocess
import tempfile
from collections.abc import Sequence
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import cast

from rich.console import Console

from maker_guide.astro_shared.theme import copy_site_theme
from maker_guide.config import DEFAULT_CONFIG_PATH, ConfigError, load_database_path
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG, DEFAULT_COURSE, DEFAULT_COURSE_ID
from maker_guide.curriculum.documentation import released_quest_index_text
from maker_guide.deployment import REGISTRATION_STATE_FILE
from maker_guide.repositories.course_release import get_course_release
from maker_guide.repositories.helpers import connect_database

_LOCAL_MARKDOWN_LINK_TARGET = re.compile(
    r"(?<=\]\()(?P<target>(?![a-z][a-z0-9+.-]*:|/|#)[^)\s]+\.md(?:#[^)\s]+)?)",
)


class DocsBuildError(ValueError):
    """Raised when the classroom documentation site cannot be built."""


def main(arguments: Sequence[str] | None = None) -> int:
    """Build and publish the static classroom documentation site."""
    parser = argparse.ArgumentParser(description="Build the classroom documentation site.")
    _ = parser.add_argument("--makers-root", type=Path, default=Path("/makers"))
    _ = parser.add_argument("--output", type=Path, required=True)
    _ = parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    _ = parser.add_argument("--database", type=Path)
    _ = parser.add_argument("--released-through")
    parsed_arguments = parser.parse_args(arguments)
    makers_root = cast("Path", parsed_arguments.makers_root).expanduser()
    output = cast("Path", parsed_arguments.output).expanduser()
    released_through = cast("str | None", parsed_arguments.released_through)
    try:
        released_through = released_through or _released_session(
            cast("Path", parsed_arguments.config),
            cast("Path | None", parsed_arguments.database),
        )
        _build(makers_root, output, released_through)
    except (ConfigError, DocsBuildError, sqlite3.Error, subprocess.CalledProcessError) as error:
        Console(stderr=True).print(_error_message(error))
        return 1
    return 0


def _build(makers_root: Path, output: Path, released_through: str | None) -> None:
    output.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{output.name}-", dir=output.parent
    ) as temporary_name:
        temporary_directory = Path(temporary_name)
        site_directory = temporary_directory / "site"
        _copy_site(site_directory)
        _copy_curriculum(site_directory / "app" / "content", released_through)
        _write_students(site_directory / "app" / "students.json", makers_root)
        _write_rankings(site_directory / "app" / "rankings.json", makers_root)
        _write_site_data(site_directory / "app" / "site-data.json", released_through)
        _run(("npm", "ci"), site_directory)
        _run(("npm", "run", "build"), site_directory)
        _export_slides(site_directory / "app" / "content", site_directory / "dist")
        _publish(site_directory / "dist", output, temporary_directory / "previous")


def _copy_site(destination: Path) -> None:
    site = resources.files("maker_guide.docs_site").joinpath("site")
    with resources.as_file(site) as site_path:
        shutil.copytree(site_path, destination)
    copy_site_theme(destination / "app" / "styles" / "site.css")


def _released_session(configuration_path: Path, database_path: Path | None) -> str | None:
    """Return the session currently released to the cohort."""
    selected_database_path = database_path or load_database_path(configuration_path)
    with connect_database(selected_database_path) as database_connection:
        course_release = get_course_release(database_connection, DEFAULT_COURSE_ID)
    return None if course_release is None else course_release.session_reached


def _copy_curriculum(destination: Path, released_through: str | None) -> None:
    """Copy the open reference library and release-gated sessions and quests."""
    curriculum = resources.files("maker_guide.curriculum").joinpath("content")
    with resources.as_file(curriculum) as curriculum_path:
        course_root = curriculum_path / DEFAULT_COURSE_ID
        for directory_name in ("commands", "concepts", "guides"):
            shutil.copytree(
                course_root / directory_name,
                destination / DEFAULT_COURSE_ID / directory_name,
            )
        if released_through is None:
            _write_course_index(destination / DEFAULT_COURSE_ID / "README.md", None)
            _rewrite_markdown_links(destination / DEFAULT_COURSE_ID)
            return
        DEFAULT_CATALOG.session(released_through)
        for relative_path in _released_content_paths(course_root, released_through):
            target_path = destination / DEFAULT_COURSE_ID / relative_path
            target_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            shutil.copy2(course_root / relative_path, target_path)
        target_path = destination / DEFAULT_COURSE_ID / "quests" / "README.md"
        target_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        target_path.write_text(
            released_quest_index_text(DEFAULT_CATALOG, released_through),
            encoding="utf-8",
        )
    _write_course_index(destination / DEFAULT_COURSE_ID / "README.md", released_through)
    _rewrite_markdown_links(destination / "lf2607")


def _released_content_paths(course_root: Path, released_through: str) -> tuple[Path, ...]:
    """Return documents reachable from released sessions and quests."""
    released_sessions = DEFAULT_COURSE.sessions[
        : next(
            session_index + 1
            for session_index, session in enumerate(DEFAULT_COURSE.sessions)
            if session.id == released_through
        )
    ]
    content_paths = {
        Path(content.path.removeprefix(f"content/{DEFAULT_COURSE_ID}/"))
        for session in released_sessions
        for content in session.content
    }
    content_paths.update(
        Path(content.path.removeprefix(f"content/{DEFAULT_COURSE_ID}/"))
        for quest in DEFAULT_CATALOG.quests_available_through(released_through)
        for content in quest.docs
    )
    pending_paths = list(content_paths)
    while pending_paths:
        relative_path = pending_paths.pop()
        markdown_text = (course_root / relative_path).read_text(encoding="utf-8")
        for link_match in _LOCAL_MARKDOWN_LINK_TARGET.finditer(markdown_text):
            linked_path = _linked_content_path(relative_path, link_match.group("target"))
            if linked_path.is_relative_to(".."):
                continue
            if linked_path not in content_paths and (course_root / linked_path).is_file():
                content_paths.add(linked_path)
                pending_paths.append(linked_path)
    return tuple(sorted(content_paths))


def _linked_content_path(relative_path: Path, link_target: str) -> Path:
    """Resolve a package-relative Markdown link without leaving course content."""
    document_path, _separator, _anchor = link_target.partition("#")
    return Path(posixpath.normpath((relative_path.parent / document_path).as_posix()))


def _write_course_index(destination: Path, released_through: str | None) -> None:
    """Generate release-filtered coursework and open-reference navigation."""
    sections = [f"# {DEFAULT_COURSE.title}", ""]
    if released_through is None:
        sections.extend(
            (
                "Session material will be published when the first session begins.",
                "",
                "## Reference Cards",
                "",
                "- [Commands](/docs/commands/README.md/)",
                "- [Concepts](/docs/concepts/README.md/)",
                "- [Guides](/docs/guides/docs-map.md/)",
            ),
        )
        destination.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        destination.write_text("\n".join(sections), encoding="utf-8")
        return
    for session in DEFAULT_COURSE.sessions:
        sections.extend((f"## {session.id}: {session.title}", ""))
        for content in session.content:
            if content.audience == "instructor":
                continue
            path = content.path.removeprefix(f"content/{DEFAULT_COURSE_ID}/")
            sections.append(f"- [{content.title}](/docs/{path}/)")
        sections.append("")
        if session.id == released_through:
            break
    sections.extend(
        (
            "## Reference Cards",
            "",
            "- [Commands](/docs/commands/README.md/)",
            "- [Concepts](/docs/concepts/README.md/)",
            "- [Guides](/docs/guides/docs-map.md/)",
            "- [Quests](/docs/quests/)",
        ),
    )
    destination.write_text("\n".join(sections), encoding="utf-8")


def _rewrite_markdown_links(content_root: Path) -> None:
    for markdown_path in sorted(content_root.rglob("*.md")):
        relative_path = markdown_path.relative_to(content_root)
        markdown_path.write_text(
            _rewrite_markdown_link_targets(
                markdown_path.read_text(encoding="utf-8"),
                relative_path,
            ),
            encoding="utf-8",
        )


def _rewrite_markdown_link_targets(markdown_text: str, relative_path: Path) -> str:
    return _LOCAL_MARKDOWN_LINK_TARGET.sub(
        lambda link_match: _absolute_docs_site_link(
            link_match.group("target"),
            relative_path,
        ),
        markdown_text,
    )


def _absolute_docs_site_link(link_target: str, relative_path: Path) -> str:
    document_path, separator, anchor = link_target.partition("#")
    absolute_document_path = posixpath.normpath(
        posixpath.join(relative_path.parent.as_posix(), document_path),
    )
    return f"/docs/{absolute_document_path}/{separator}{anchor}"


def _write_students(destination: Path, makers_root: Path) -> None:
    students = [student_directory.name for student_directory in _student_directories(makers_root)]
    destination.write_text(f"{json.dumps(students)}\n", encoding="utf-8")


def _write_rankings(destination: Path, makers_root: Path) -> None:
    rankings = sorted(
        (
            {
                "handle": student_directory.name,
                "rank": int((student_directory / "rank").read_text(encoding="utf-8")),
                "score": int((student_directory / "score").read_text(encoding="utf-8")),
            }
            for student_directory in _student_directories(makers_root)
        ),
        key=lambda ranking: ranking["rank"],
    )
    destination.write_text(f"{json.dumps(rankings)}\n", encoding="utf-8")


def _write_site_data(destination: Path, released_through: str | None) -> None:
    current_session = (
        None if released_through is None else DEFAULT_CATALOG.session(released_through)
    )
    site_data = {
        "current_session": None
        if current_session is None
        else {
            "date": current_session.date.isoformat(),
            "materials": [
                {
                    "path": "/docs/"
                    + content.path.removeprefix(f"content/{DEFAULT_COURSE.id}/")
                    + "/",
                    "title": content.title,
                }
                for content in current_session.content
                if content.audience != "instructor"
            ],
            "title": current_session.title,
        },
        "rankings_updated_at": datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "registration_open": Path(REGISTRATION_STATE_FILE).is_file(),
    }
    destination.write_text(
        f"{json.dumps(site_data)}\n",
        encoding="utf-8",
    )


def _student_directories(makers_root: Path) -> list[Path]:
    if not makers_root.is_dir():
        return []
    return sorted(
        (
            student_directory
            for student_directory in makers_root.iterdir()
            if (
                student_directory.is_dir()
                and not student_directory.is_symlink()
                and (student_directory / "rank").is_file()
            )
        ),
        key=lambda student_directory: student_directory.name,
    )


def _publish(source: Path, output: Path, previous: Path) -> None:
    if output.exists():
        output.replace(previous)
    try:
        source.replace(output)
    except Exception:
        if previous.exists():
            previous.replace(output)
        raise
    shutil.rmtree(previous, ignore_errors=True)


def _export_slides(content_root: Path, output_root: Path) -> None:
    for slides_path in sorted((content_root / DEFAULT_COURSE_ID / "sessions").glob("*/slides.md")):
        output_path = (
            output_root
            / "docs"
            / slides_path.relative_to(content_root / DEFAULT_COURSE_ID)
            / "index.html"
        )
        command = shlex.join(
            (
                "presenterm",
                "--export-html",
                "--output",
                str(output_path),
                str(slides_path),
            )
        )
        # ponytail: Presenterm 0.16.1 needs a terminal during HTML export. Remove this
        # wrapper after a release includes https://github.com/mfontanini/presenterm/pull/857.
        _ = subprocess.run(  # noqa: S603 - fixed tools with shell-escaped paths.
            ("/usr/bin/script", "-qefc", f"stty rows 40 cols 100 && {command}", "/dev/null"),
            check=True,
            cwd=output_root.parent,
            input="\x1b[?c\x1b[1;1R",
            stdout=subprocess.DEVNULL,
            text=True,
        )


def _run(command: tuple[str, ...], destination: Path) -> None:
    _ = subprocess.run(command, check=True, cwd=destination)  # noqa: S603 - fixed tool commands.


def _error_message(
    error: ConfigError | DocsBuildError | sqlite3.Error | subprocess.CalledProcessError,
) -> str:
    if not isinstance(error, subprocess.CalledProcessError):
        return str(error)
    command = cast("Sequence[object]", error.cmd)
    return f"{' '.join(str(part) for part in command)} failed with status {error.returncode}"
