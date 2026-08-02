"""Tests for documentation link checking CLI."""

from __future__ import annotations

from pathlib import Path

from maker_guide.cli.check_doc_links import MissingDocReference, find_missing_doc_references, run


def test_find_missing_doc_references_reports_missing_targets(temporary_path: Path) -> None:
    """The checker maps `/docs/...md` links to the selected documents root."""
    documents_root = temporary_path / "docs"
    (documents_root / "concepts").mkdir(parents=True)
    (documents_root / "concepts" / "source.md").write_text(
        "[ok](/docs/concepts/source.md)\n[missing](/docs/concepts/missing.md)\n",
        encoding="utf-8",
    )

    assert find_missing_doc_references(documents_root) == [
        MissingDocReference(
            source_path=documents_root / "concepts" / "source.md",
            line_number=2,
            target="/docs/concepts/missing.md",
        ),
    ]


def test_find_missing_doc_references_ignores_template_paths(temporary_path: Path) -> None:
    """Shell variables and template placeholders do not name literal docs files."""
    documents_root = temporary_path / "docs"
    documents_root.mkdir()
    (documents_root / "index.md").write_text(
        """presenterm /docs/sessions/$SESSION_ID/slides.md
[template](/docs/sessions/{session_id}/slides.md)
""",
        encoding="utf-8",
    )

    assert find_missing_doc_references(documents_root) == []


def test_check_doc_links_cli_exits_nonzero_for_missing_targets(temporary_path: Path) -> None:
    """The CLI fails when a referenced `/docs/...md` file is absent."""
    documents_root = temporary_path / "docs"
    documents_root.mkdir()
    (documents_root / "index.md").write_text("[missing](/docs/nope.md)\n", encoding="utf-8")

    assert run(["--documents-root", str(documents_root)]) == 1


def test_check_doc_links_cli_accepts_reachable_targets(temporary_path: Path) -> None:
    """The CLI succeeds when every `/docs/...md` reference exists."""
    documents_root = temporary_path / "docs"
    documents_root.mkdir()
    (documents_root / "index.md").write_text("[self](/docs/index.md)\n", encoding="utf-8")

    assert run(["--documents-root", str(documents_root)]) == 0
