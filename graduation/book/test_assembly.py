"""Check editable course content without accessing purchased artwork."""

from pathlib import Path

import pymupdf

from assemble import MILLIMETER, add_foreword
from print_export import BLEED, add_bleed


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


def test_bleed_preserves_artwork_and_blank_faces(tmp_path: Path) -> None:
    """Bleed shifts, never scales, artwork; unprinted cover faces stay blank."""
    source = tmp_path / "source.pdf"
    output = tmp_path / "bleed.pdf"
    with pymupdf.open() as document:
        page = document.new_page(width=210 * MILLIMETER, height=148 * MILLIMETER)
        page.insert_text((50, 60), "Vector artwork", fontsize=12)
        page.draw_line((60, 80), (160, 80))
        document.new_page(width=210 * MILLIMETER, height=148 * MILLIMETER)
        document.save(source)
    add_bleed(source, output, (0,))
    with pymupdf.open(source) as original, pymupdf.open(output) as printed:
        assert len(printed) == 2
        for page in printed:
            assert abs(page.rect.width / MILLIMETER - 216) < 0.001
            assert abs(page.rect.height / MILLIMETER - 154) < 0.001
            assert abs(page.trimbox.width / MILLIMETER - 210) < 0.001
            assert abs(page.trimbox.height / MILLIMETER - 148) < 0.001
            assert page.bleedbox == page.mediabox
        assert printed[0].get_textpage().extractText() == original[0].get_textpage().extractText()
        before = original[0].get_textpage().extractBLOCKS()[0]
        after = printed[0].get_textpage().extractBLOCKS()[0]
        for position in range(4):
            assert abs(after[position] - before[position] - BLEED) < 0.01
        assert len(printed[0].get_drawings()) == 2
        assert not printed[1].get_contents()


if __name__ == "__main__":
    test_approved_foreword_fits()
    print("Approved foreword layout passed")
