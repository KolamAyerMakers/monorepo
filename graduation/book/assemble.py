"""Build local review proofs, retaining purchased artwork as PDF objects."""

import argparse
import json
import os
import subprocess
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

MILLIMETER = 72 / 25.4
BOOKS = (
    ("The Secret Rules of the Terminal", "terminal", 28),
    ("Bite Size Command Line", "command-line", 24),
    ("Bite Size Linux", "linux", 24),
    ("Bite Size Bash", "bash", 28),
    ("How Git Works", "git", 28),
)


def text(
    page: pymupdf.Page,
    position: tuple[float, float],
    value: str,
    size: float = 11,
    bold: bool = False,
) -> None:
    page.insert_font(
        fontname="LiberationBold" if bold else "Liberation",
        fontfile=str(
            Path("/usr/share/fonts/truetype/liberation/")
            / ("LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf")
        ),
    )
    page.insert_text(
        position,
        value,
        fontsize=size,
        fontname="LiberationBold" if bold else "Liberation",
        color=(0, 0, 0),
    )


def add_foreword(page: pymupdf.Page) -> None:
    """Place the approved text and signature without shrinking to hide overflow."""
    text(page, (50, 65), "Keep It Going", 27, True)
    body = Path(__file__).with_name("foreword.txt").read_text().strip()
    if "\u2014" in body:
        raise ValueError("The approved foreword must not contain em dashes")
    page.insert_font(
        fontname="Liberation",
        fontfile="/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    )
    bottom = page.rect.height - 72
    remaining = page.insert_textbox(
        pymupdf.Rect(50, 92, page.rect.width - 50, bottom),
        body,
        fontname="Liberation",
        fontsize=11,
        lineheight=1.25,
        color=(0, 0, 0),
    )
    if remaining < 0:
        raise ValueError("Foreword does not fit at the intended reading size")
    signature_baseline = bottom - remaining + 23
    text(page, (50, signature_baseline), "Philippe Muller", 11, True)
    page.insert_font(
        fontname="LiberationMono",
        fontfile="/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
    )
    # Darker print counterparts of the website's yellow, teal and lime.
    position = 50.0
    for word, color in (
        ("Build.", (0.48, 0.37, 0.0)),
        ("Break.", (0.0, 0.38, 0.35)),
        ("Repeat.", (0.27, 0.36, 0.0)),
    ):
        page.insert_text(
            (position, signature_baseline + 19),
            word,
            fontname="LiberationMono",
            fontsize=11,
            color=color,
        )
        position += (len(word) + 1) * 6.6


def build(
    source: Path, output: Path, width: float, height: float, gutter: float, outer: float
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    interior = pymupdf.open()
    for page_number in range(2):
        interior.new_page(width=width * MILLIMETER, height=height * MILLIMETER)
    add_foreword(interior[0])
    text(interior[1], (50, 65), "Five guides to explore", 25, True)
    for baseline, note in (
        (330, "Each guide by Julia Evans is complete, with its original covers and credits."),
        (347, "Original page numbers remain unchanged. Contents refer to interior positions."),
        (364, "The foreword, this contents page and outer covers are course additions."),
        (391, "Local production proof. Do not distribute the PDF to students."),
    ):
        text(interior[1], (50, baseline), note, 10)
    manifest = []
    bookmarks = [
        [1, "Keep It Going", 1],
        [1, "Contents", 2],
    ]
    for index, (title, slug, count) in enumerate(BOOKS):
        matches = [
            path for path in source.rglob("*.pdf") if path.name == f"{title} - Wizard Zines.pdf"
        ]
        if len(matches) != 1:
            raise ValueError(f"Expected one purchased source for {title}: {matches}")
        with pymupdf.open(matches[0]) as document:
            if len(document) != count:
                raise ValueError(f"Unexpected logical page count for {title}")
            start = len(interior) + 1
            bookmarks.append([1, title, start])
            text(interior[1], (50, 115 + index * 42), f"{index + 1:02}   {title}", 13)
            text(interior[1], (520, 115 + index * 42), str(start), 13)
            manifest.append(
                {
                    "title": title,
                    "source": str(matches[0].relative_to(source)),
                    "pages": count,
                    "interior_start": start,
                    "interior_end": start + count - 1,
                }
            )
            for logical in range(len(document)):
                page = interior.new_page(width=width * MILLIMETER, height=height * MILLIMETER)
                # Physical binding edge is left on rectos and right on versos.
                left, right = (gutter, outer) if len(interior) % 2 else (outer, gutter)
                page.show_pdf_page(
                    pymupdf.Rect(
                        left * MILLIMETER,
                        outer * MILLIMETER,
                        (width - right) * MILLIMETER,
                        (height - outer) * MILLIMETER,
                    ),
                    document,
                    logical,
                )
    interior.set_toc(bookmarks)
    interior.set_metadata(
        {
            "title": "At the Prompt | PROVISIONAL REVIEW",
            "author": "Julia Evans; course additions by Philippe Muller",
            "subject": "Not approved for production",
        }
    )
    interior.save(output / "at-the-prompt-interior-PROVISIONAL.pdf", garbage=4, deflate=True)
    with pymupdf.open() as covers:
        for name in ("front", "back"):
            subprocess.run(
                [
                    "inkscape",
                    f"{name}.svg",
                    "--export-type=pdf",
                    f"--export-filename={output / (name + '.pdf')}",
                ],
                check=True,
                env={
                    **os.environ,
                    "NO_AT_BRIDGE": "1",
                    "FONTCONFIG_FILE": str(
                        Path(__file__).resolve().parent / "fonts/fontconfig.xml"
                    ),
                },
            )
            with pymupdf.open(output / f"{name}.pdf") as vector:
                covers.insert_pdf(vector)
                if name == "front":
                    for face in range(2):
                        covers.new_page(width=vector[0].rect.width, height=vector[0].rect.height)
        covers.save(output / "at-the-prompt-covers-PROVISIONAL.pdf", garbage=4, deflate=True)
        with pymupdf.open() as proof:
            proof.insert_pdf(covers, from_page=0, to_page=1)
            proof.insert_pdf(interior)
            proof.insert_pdf(covers, from_page=2, to_page=3)
            proof.set_toc([[level, title, number + 2] for level, title, number in bookmarks])
            proof.set_metadata({"title": "At the Prompt | PROVISIONAL REVIEW"})
            proof.save(output / "at-the-prompt-review-PROVISIONAL.pdf", garbage=4, deflate=True)
    with pymupdf.open() as samples:
        for number in (9, 26, 35, 39, 62, 68, 89, 103, 120, 131):
            samples.insert_pdf(interior, from_page=number - 1, to_page=number - 1)
        samples.save(output / "at-the-prompt-actual-size-samples-A5.pdf", garbage=4, deflate=True)
    (output / "pagination.json").write_text(
        json.dumps(
            {
                "format_mm": [width, height],
                "gutter_mm": gutter,
                "outer_mm": outer,
                "interior_pages": len(interior),
                "proof_pages": len(interior) + 4,
                "cover_faces": ["front", "inside front (blank)", "inside back (blank)", "back"],
                "books": manifest,
                "sample_interior_pages": [9, 26, 35, 39, 62, 68, 89, 103, 120, 131],
            },
            indent=2,
        )
        + "\n"
    )
    render(interior, output / "rendered")
    interior.close()


def render(document: pymupdf.Document, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(document), 16):
        sheet = Image.new("RGB", (1600, 1200), "white")
        labels = ImageDraw.Draw(sheet)
        for index in range(start, min(start + 16, len(document))):
            page = document[index]
            preview = page.get_pixmap(dpi=150, alpha=False)
            preview.save(output / f"page-{index + 1:03}.png")
            thumbnail = Image.frombytes("RGB", (preview.width, preview.height), preview.samples)
            thumbnail.thumbnail((390, 275))
            sheet.paste(thumbnail, (((index - start) % 4) * 400, ((index - start) // 4) * 300 + 20))
            labels.text(
                (((index - start) % 4) * 400, ((index - start) // 4) * 300),
                str(index + 1),
                fill="black",
            )
        sheet.save(output / f"contact-{start + 1:03}.jpg")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("local/proofs"))
    parser.add_argument("--width", type=float, default=210)
    parser.add_argument("--height", type=float, default=148)
    parser.add_argument("--gutter", type=float, default=12)
    parser.add_argument("--outer", type=float, default=5)
    arguments = parser.parse_args()
    if min(arguments.width, arguments.height, arguments.gutter, arguments.outer) <= 0:
        parser.error("Dimensions and margins must be positive")
    if (
        arguments.width <= arguments.gutter + arguments.outer
        or arguments.height <= 2 * arguments.outer
    ):
        parser.error("Margins consume the entire page")
    build(
        arguments.source,
        arguments.output,
        arguments.width,
        arguments.height,
        arguments.gutter,
        arguments.outer,
    )
