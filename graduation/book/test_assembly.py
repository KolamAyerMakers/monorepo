"""Check editable course content without accessing purchased artwork."""

from pathlib import Path

import pymupdf

from assemble import MILLIMETER, add_foreword


def test_approved_foreword_fits() -> None:
    """The complete approved text and motto fit on A5 without em dashes."""
    with pymupdf.open() as document:
        page = document.new_page(width=210 * MILLIMETER, height=148 * MILLIMETER)
        add_foreword(page)
        extracted = " ".join(page.get_textpage().extractText().split())
        approved = " ".join(Path(__file__).with_name("foreword.txt").read_text().split())
        assert extracted == f"Keep It Going {approved} Philippe Muller Build. Break. Repeat."
        assert "\u2014" not in extracted
        for block in page.get_textpage().extractDICT()["blocks"]:
            if block["type"] == 0:
                assert pymupdf.Rect(block["bbox"]) in page.rect


if __name__ == "__main__":
    test_approved_foreword_fits()
    print("Approved foreword layout passed")
