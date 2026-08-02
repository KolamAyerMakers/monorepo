"""Helpers that map curriculum metadata to learner documentation."""

from __future__ import annotations

import posixpath
from importlib.resources import abc, files

from maker_guide.curriculum.models import CourseCatalog, Quest

_COMMAND_CARD_SLUGS = {
    ">": "redirect",
    ">>": "append-redirection",
    "2>": "stderr-redirect",
    "2>>": "stderr-redirect",
    "2>&1": "stderr-to-stdout",
    "ls -l": "ls-l",
    "rm -i": "rm",
    "rm -rf": "rm",
    "chmod +x": "chmod",
    "set -euo pipefail": "set",
    "then": "if",
    "else": "if",
    "fi": "if",
    "[[ ]]": "double-brackets",
    "curl -I": "curl-head",
    "curl -v": "curl-verbose",
    "python3 -m http.server --bind 127.0.0.1": "python3-http-server",
    "id -u": "id-u",
    "systemctl --user": "systemctl",
    "journalctl --user": "journalctl",
    "systemd timer": "systemd-timer",
    "systemctl --user list-timers": "systemctl-list-timers",
}

type _IndexEntry = tuple[str, str]


def command_card_slug(command: str) -> str:
    """Return the command card slug for a catalog command form."""
    return _COMMAND_CARD_SLUGS.get(command, command.replace(" ", "-"))


def document_title(resource: abc.Traversable) -> str:
    """Return the first Markdown heading, falling back to the filename."""
    for line in resource.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return resource.name.removesuffix(".md")


def released_quest_index_text(
    catalog: CourseCatalog,
    released_through: str,
) -> str:
    """Render release-filtered quest navigation."""
    lines = [
        files("maker_guide.curriculum")
        .joinpath(
            "content",
            catalog.course.id,
            "quests",
            "README.md",
        )
        .read_text(encoding="utf-8")
        .partition("\n## ")[0]
        .rstrip(),
        "",
    ]
    for session in catalog.sessions_through(released_through):
        entries = tuple(
            _quest_document_entry(catalog.course.id, quest)
            for quest in catalog.quests_available_after(session.id)
        )
        if not entries:
            continue
        lines.extend((f"## {session.id}: {session.title}", ""))
        lines.extend(f"- [{label}]({target})" for label, target in entries)
        lines.append("")
    return "\n".join(lines)


def _quest_document_entry(course_id: str, quest: Quest) -> _IndexEntry:
    return quest.id, posixpath.relpath(
        next(
            reference.path for reference in quest.docs if reference.purpose == "quest"
        ).removeprefix(f"content/{course_id}/"),
        start="quests",
    )
