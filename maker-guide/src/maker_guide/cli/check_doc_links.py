"""Check learner documentation links."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, cast

import typer
from rich.console import Console

app = typer.Typer(
    add_completion=False,
    help="Check that `/docs/...md` references point at existing files.",
    pretty_exceptions_enable=False,
)

_DOCS_REFERENCE = re.compile(r"(?P<target>/docs/[^)\]\s#?${<]+\.md)")


@dataclass(frozen=True, slots=True)
class MissingDocReference:
    """A `/docs/...md` reference whose target does not exist."""

    source_path: Path
    line_number: int
    target: str


def run(arguments: Sequence[str] | None = None) -> int:
    """Run the Typer app for tests."""
    result = cast(
        "object",
        app(
            args=list(arguments) if arguments is not None else None,
            standalone_mode=False,
        ),
    )
    if isinstance(result, int):
        return result
    return 0


@app.command()
def check(
    documents_root: Annotated[
        Path,
        typer.Option("--documents-root", help="Root directory mounted as `/docs`."),
    ] = Path("/docs"),
) -> None:
    """Check all Markdown files under `/docs`."""
    missing_references = find_missing_doc_references(documents_root.expanduser())
    if missing_references:
        for missing_reference in missing_references:
            Console(stderr=True).print(
                (
                    f"{missing_reference.source_path}:{missing_reference.line_number}: "
                    f"missing {missing_reference.target}"
                ),
            )
        raise typer.Exit(1)

    Console().print("All /docs Markdown references are reachable.")


def find_missing_doc_references(documents_root: Path) -> list[MissingDocReference]:
    """Return missing `/docs/...md` references below the docs root."""
    return [
        missing_reference
        for source_path in sorted(documents_root.rglob("*.md"))
        for missing_reference in _missing_references_in_file(documents_root, source_path)
    ]


def _missing_references_in_file(
    documents_root: Path,
    source_path: Path,
) -> list[MissingDocReference]:
    return [
        MissingDocReference(source_path=source_path, line_number=line_number, target=target)
        for line_number, line in enumerate(source_path.read_text(encoding="utf-8").splitlines(), 1)
        for target in _targets_from_line(line)
        if not (documents_root / target.removeprefix("/docs/")).exists()
    ]


def _targets_from_line(line: str) -> set[str]:
    return {match.group("target") for match in _DOCS_REFERENCE.finditer(line)}
