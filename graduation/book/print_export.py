"""Add the printer's 3 mm bleed without scaling or rasterising the approved proof."""

import argparse
from pathlib import Path

import pymupdf

from assemble import MILLIMETER

BLEED = 3 * MILLIMETER
COVER_BACKGROUND = (244 / 255, 240 / 255, 230 / 255)  # #f4f0e6 in front.svg/back.svg


def add_bleed(source: Path, output: Path, cover_faces: tuple[int, ...] = ()) -> None:
    """Keep artwork at trim size; extend only the outer covers' ivory background."""
    with pymupdf.open(source) as original, pymupdf.open() as result:
        for index, original_page in enumerate(original):
            if original_page.rotation or any(
                abs(actual - expected * MILLIMETER) > 0.1
                for actual, expected in zip(
                    (original_page.rect.width, original_page.rect.height), (210, 148)
                )
            ):
                raise ValueError(
                    f"Expected unrotated 210 × 148 mm pages: {source}, page {index + 1}"
                )
            page = result.new_page(
                width=original_page.rect.width + 2 * BLEED,
                height=original_page.rect.height + 2 * BLEED,
            )
            trim = pymupdf.Rect(BLEED, BLEED, page.rect.width - BLEED, page.rect.height - BLEED)
            if index in cover_faces:
                page.draw_rect(page.rect, color=None, fill=COVER_BACKGROUND)
            if original_page.get_contents():
                page.show_pdf_page(trim, original, index)
            page.set_trimbox(trim)
            page.set_bleedbox(page.mediabox)
        result.set_toc(original.get_toc())
        result.set_metadata(
            {
                "title": "At the Prompt | 3 mm bleed | printer approval pending",
                "author": "Julia Evans; course additions by Philippe Muller",
                "subject": "210 × 148 mm trim; 3 mm bleed; no crop marks; not certified PDF/X",
            }
        )
        result.save(output, garbage=4, deflate=True)


def export(proofs: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for name, count, cover_faces in (
        ("review", 138, (0, 137)),
        ("interior", 134, ()),
        ("covers", 4, (0, 3)),
    ):
        source = proofs / f"at-the-prompt-{name}-PROVISIONAL.pdf"
        with pymupdf.open(source) as document:
            if len(document) != count:
                raise ValueError(f"Expected {count} pages: {source}")
        add_bleed(source, output / f"at-the-prompt-{name}-3mm-bleed-PROVISIONAL.pdf", cover_faces)
    for name in ("front", "back"):
        add_bleed(proofs / f"{name}.pdf", output / f"{name}-3mm-bleed-PROVISIONAL.pdf", (0,))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("local/proofs"))
    parser.add_argument("--output", type=Path, default=Path("local/print"))
    arguments = parser.parse_args()
    export(arguments.input, arguments.output)
