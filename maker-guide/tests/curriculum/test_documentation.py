"""Tests for curriculum documentation helpers."""

from __future__ import annotations

from dataclasses import replace

import pytest

from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.curriculum.documentation import command_card_slug, released_quest_index_text
from maker_guide.curriculum.models import CourseCatalog


@pytest.mark.parametrize(
    ("command", "expected_slug"),
    [
        (">", "redirect"),
        (">>", "append-redirection"),
        ("2>", "stderr-redirect"),
        ("2>>", "stderr-redirect"),
        ("2>&1", "stderr-to-stdout"),
        ("ls -l", "ls-l"),
        ("rm -i", "rm"),
        ("rm -rf", "rm"),
        ("chmod +x", "chmod"),
        ("set -euo pipefail", "set"),
        ("then", "if"),
        ("else", "if"),
        ("fi", "if"),
        ("[[ ]]", "double-brackets"),
        ("curl -I", "curl-head"),
        ("curl -v", "curl-verbose"),
        ("python3 -m http.server --bind 127.0.0.1", "python3-http-server"),
        ("id -u", "id-u"),
        ("systemctl --user", "systemctl"),
        ("journalctl --user", "journalctl"),
        ("systemd timer", "systemd-timer"),
        ("systemctl --user list-timers", "systemctl-list-timers"),
        ("git status", "git-status"),
        ("whoami", "whoami"),
    ],
)
def test_command_card_slug_resolves_catalog_forms(command: str, expected_slug: str) -> None:
    """Command syntax resolves to the card that teaches it."""
    assert command_card_slug(command) == expected_slug


def test_released_quest_index_uses_catalog_document_path() -> None:
    """Quest navigation follows the catalog reference rather than an id convention."""
    first_quest = CATALOG.course.quests[0]
    catalog = CourseCatalog(
        replace(
            CATALOG.course,
            quests=(
                replace(
                    first_quest,
                    docs=(
                        replace(
                            first_quest.docs[0],
                            path=f"content/{CATALOG.course.id}/quests/custom-proof.md",
                        ),
                    ),
                ),
                *CATALOG.course.quests[1:],
            ),
        ),
    )

    assert "(custom-proof.md)" in released_quest_index_text(catalog, "S1")
