"""Tests for the classroom documentation site builder."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pytest

from maker_guide.cli import build_docs
from maker_guide.cli.check_doc_links import find_missing_doc_references

_LOCAL_DOCUMENT_HREF: re.Pattern[str] = re.compile(
    r'href="(?P<target>(?![a-z][a-z0-9+.-]*:)[^"#?]+\.md/?)(?:#[^"]*)?"',
)


def test_build_docs_packages_curriculum_and_publishes_site(  # noqa: PLR0915 - One build transaction.
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The builder installs pinned dependencies and atomically publishes static HTML."""
    commands: list[tuple[Sequence[str], Path]] = []
    rankings_content = ""
    site_data_content = ""
    students_content = ""
    readme_content = ""
    theme_content = ""
    session_two_exists = False
    curriculum_indexes: dict[str, str] = {}

    def run(
        command: Sequence[str], **keyword_arguments: object
    ) -> subprocess.CompletedProcess[str]:
        nonlocal rankings_content, readme_content, session_two_exists, site_data_content
        nonlocal students_content, theme_content
        working_directory = keyword_arguments["cwd"]
        assert isinstance(working_directory, Path)
        commands.append((command, working_directory))
        if command == ("npm", "ci"):
            curriculum_root = working_directory / "app" / "content" / "lf2607"
            students_content = (working_directory / "app" / "students.json").read_text(
                encoding="utf-8"
            )
            rankings_content = (working_directory / "app" / "rankings.json").read_text(
                encoding="utf-8"
            )
            site_data_content = (working_directory / "app" / "site-data.json").read_text(
                encoding="utf-8"
            )
            readme_content = (curriculum_root / "README.md").read_text(encoding="utf-8")
            curriculum_indexes.update(
                {
                    directory_name: (curriculum_root / directory_name / "README.md").read_text(
                        encoding="utf-8"
                    )
                    for directory_name in ("commands", "concepts", "quests")
                }
            )
            theme_content = (working_directory / "app" / "styles" / "site.css").read_text(
                encoding="utf-8"
            )
            session_two_exists = (
                working_directory / "app" / "content" / "lf2607" / "sessions" / "S02"
            ).exists()
        if command == ("npm", "run", "build"):
            for relative_path, content in (
                ("index.html", "home"),
                ("docs/index.html", "course"),
            ):
                output_page = working_directory / "dist" / relative_path
                output_page.parent.mkdir(parents=True, exist_ok=True)
                output_page.write_text(content, encoding="utf-8")
        if command[0] == "/usr/bin/script":
            slides_page = (
                working_directory
                / "dist"
                / "docs"
                / "sessions"
                / "S01"
                / "slides.md"
                / "index.html"
            )
            slides_page.parent.mkdir(parents=True, exist_ok=True)
            slides_page.write_text("presenterm", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", run)
    output = temporary_path / "site"
    makers_root = temporary_path / "makers"
    registration_state_file = temporary_path / "registration-open"
    monkeypatch.setattr(build_docs, "REGISTRATION_STATE_FILE", str(registration_state_file))
    (makers_root / "ada").mkdir(parents=True)
    (makers_root / "ada" / "rank").write_text("2\n", encoding="utf-8")
    (makers_root / "ada" / "score").write_text("7\n", encoding="utf-8")
    (makers_root / "mohd").mkdir()
    (makers_root / "mohd" / "rank").write_text("1\n", encoding="utf-8")
    (makers_root / "mohd" / "score").write_text("11\n", encoding="utf-8")

    assert (
        build_docs.main(
            [
                "--makers-root",
                str(makers_root),
                "--output",
                str(output),
                "--released-through",
                "S1",
            ],
        )
        == 0
    )
    assert (output / "index.html").read_text(encoding="utf-8") == "home"
    assert (output / "docs" / "index.html").read_text(encoding="utf-8") == "course"
    assert (output / "docs" / "sessions" / "S01" / "slides.md" / "index.html").read_text(
        encoding="utf-8"
    ) == "presenterm"
    assert [command for command, _working_directory in commands[:2]] == [
        ("npm", "ci"),
        ("npm", "run", "build"),
    ]
    assert len(commands) == 3
    assert commands[2][0][0:2] == ("/usr/bin/script", "-qefc")
    assert "presenterm --export-html" in commands[2][0][2]
    assert students_content == '["ada", "mohd"]\n'
    assert rankings_content == (
        '[{"handle": "mohd", "rank": 1, "score": 11}, {"handle": "ada", "rank": 2, "score": 7}]\n'
    )
    assert '"registration_open": false' in site_data_content
    assert '"rankings_updated_at": ' in site_data_content
    assert json.loads(site_data_content)["current_session"]["materials"]
    assert all(
        reference_card in readme_content
        for reference_card in (
            "- [Commands](/docs/commands/README.md/)",
            "- [Concepts](/docs/concepts/README.md/)",
            "- [Guides](/docs/guides/docs-map.md/)",
            "- [Quests](/docs/quests/)",
        )
    )
    assert "S02" not in readme_content
    assert session_two_exists is False
    assert "/docs/commands/whoami.md/" in curriculum_indexes["commands"]
    assert "/docs/commands/tmux.md/" in curriculum_indexes["commands"]
    assert "/docs/concepts/shell-basics.md/" in curriculum_indexes["concepts"]
    assert "/docs/concepts/terminal-multiplexing.md/" in curriculum_indexes["concepts"]
    assert "Go Deeper After S03" in curriculum_indexes["concepts"]
    assert "/docs/quests/prove-shell-alive.md/" in curriculum_indexes["quests"]
    assert "/docs/quests/build-playground.md/" not in curriculum_indexes["quests"]
    assert ".site-shell" in theme_content
    assert "prefers-color-scheme" in theme_content


def test_build_docs_reports_failed_tool(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A failed static-site command leaves the target untouched."""
    output = temporary_path / "site"

    def run(
        command: Sequence[str], **_keyword_arguments: object
    ) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(subprocess, "run", run)

    assert build_docs.main(["--output", str(output), "--released-through", "S1"]) == 1
    assert "npm ci failed with status 1" in capsys.readouterr().err
    assert output.exists() is False


def test_build_docs_publishes_unreleased_course_site(
    temporary_path: Path,
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unreleased course publishes future references with working links."""
    output = temporary_path / "site"
    reference_cards_exist = False
    reference_links_rewritten = False
    prerelease_links_close = False
    readme_content = ""

    def run(command: tuple[str, ...], destination: Path) -> None:
        nonlocal prerelease_links_close, readme_content, reference_cards_exist
        nonlocal reference_links_rewritten
        content = destination / "app" / "content" / "lf2607"
        if command == ("npm", "ci"):
            readme_content = (content / "README.md").read_text(encoding="utf-8")
            reference_cards_exist = all(
                (content / relative_path).is_file()
                for relative_path in (
                    Path("commands/tmux.md"),
                    Path("concepts/terminal-multiplexing.md"),
                    Path("guides/docs-map.md"),
                )
            )
            reference_links_rewritten = "/docs/concepts/terminal-multiplexing.md/" in (
                content / "commands" / "tmux.md"
            ).read_text(encoding="utf-8")
            prerelease_links_close = find_missing_doc_references(content) == []
        if command == ("npm", "run", "build"):
            (destination / "dist").mkdir()

    monkeypatch.setattr(build_docs, "_run", run)

    assert (
        build_docs.main(["--output", str(output), "--database", str(migrated_database_path)]) == 0
    )
    assert reference_cards_exist
    assert reference_links_rewritten
    assert prerelease_links_close
    assert readme_content == (
        "# Linux Foundations\n\n"
        "Session material will be published when the first session begins.\n\n"
        "## Reference Cards\n\n"
        "- [Commands](/docs/commands/README.md/)\n"
        "- [Concepts](/docs/concepts/README.md/)\n"
        "- [Guides](/docs/guides/docs-map.md/)"
    )


@pytest.mark.integration
def test_build_docs_publishes_open_reference_routes_and_gates_coursework(
    temporary_path: Path,
) -> None:
    """Future references and their links render while future coursework stays absent."""
    output = temporary_path / "site"

    assert (
        build_docs.main(
            [
                "--makers-root",
                str(temporary_path / "makers"),
                "--output",
                str(output),
                "--released-through",
                "S5",
            ],
        )
        == 0
    )

    command_index = (output / "docs" / "commands" / "index.html").read_text(encoding="utf-8")
    concept_index = (output / "docs" / "concepts" / "index.html").read_text(encoding="utf-8")
    quest_index = (output / "docs" / "quests" / "index.html").read_text(encoding="utf-8")
    assert "/docs/commands/whoami.md/" in command_index
    assert "/docs/commands/tmux.md/" in command_index
    assert "/docs/concepts/shell-basics.md/" in concept_index
    assert "/docs/concepts/terminal-multiplexing.md/" in concept_index
    assert "Go Deeper After S03" in concept_index
    assert "/docs/quests/prove-shell-alive.md/" in quest_index
    assert "/docs/quests/build-playground.md/" in quest_index
    assert "/docs/quests/measure-ping.md/" not in quest_index
    for relative_route in (
        Path("docs/commands/tmux.md/index.html"),
        Path("docs/concepts/terminal-multiplexing.md/index.html"),
        Path("docs/guides/docs-map.md/index.html"),
    ):
        assert (output / relative_route).is_file()
    for relative_route in (
        Path("docs/sessions/S06/self-study.md/index.html"),
        Path("docs/quests/measure-ping.md/index.html"),
    ):
        assert not (output / relative_route).exists()

    command_readme_page = (output / "docs" / "commands" / "README.md" / "index.html").read_text(
        encoding="utf-8"
    )
    assert re.search(r'<a href="/docs/"[^>]*>Up one level</a>', command_readme_page)
    assert not re.search(
        r'<a href="/docs/commands/README\.md/"[^>]*>Up one level</a>',
        command_readme_page,
    )
    s5_self_study_page = (
        output / "docs" / "sessions" / "S05" / "self-study.md" / "index.html"
    ).read_text(encoding="utf-8")
    assert re.search(
        r'<a href="/docs/commands/exit\.md/"[^>]*>Command: <code[^>]*>exit</code></a>',
        s5_self_study_page,
    )

    for reference_directory in ("commands", "concepts", "guides"):
        for reference_page in sorted(
            (output / "docs" / reference_directory).rglob("*.md/index.html")
        ):
            for link_target in cast(
                "list[str]",
                _LOCAL_DOCUMENT_HREF.findall(reference_page.read_text(encoding="utf-8")),
            ):
                assert link_target.startswith("/docs/"), (
                    f"{reference_page} contains non-canonical local link {link_target}"
                )
                linked_route = output / link_target.removeprefix("/").rstrip("/") / "index.html"
                assert linked_route.is_file(), f"{reference_page} links to missing {link_target}"
