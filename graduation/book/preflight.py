"""Verify page counts, preserved resources, text, and binding clearances."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import cast

import pymupdf
from PIL import Image, ImageChops

from assemble import MILLIMETER


def image_hashes(document: pymupdf.Document, number: int) -> list[str]:
    hashes = set()
    for image in document.get_page_images(number):
        for reference in (image[0], image[1]):
            if reference:
                stream = document.xref_stream(reference)
                assert stream is not None, reference
                hashes.add(hashlib.sha256(stream).hexdigest())
    return sorted(hashes)


def preflight(source: Path, output: Path) -> None:
    manifest = json.loads((output / "pagination.json").read_text())
    report = {"status": "technical review only; printer approval pending", "pages": []}
    with pymupdf.open(output / "at-the-prompt-interior-PROVISIONAL.pdf") as interior:
        assert len(interior) == manifest["interior_pages"] == 134
        for book in manifest["books"]:
            with pymupdf.open(source / book["source"]) as original:
                assert len(original) == book["pages"]
                for index in range(len(original)):
                    number = book["interior_start"] + index
                    page = interior[number - 1]
                    assert page.rotation == 0
                    assert abs(page.rect.width / MILLIMETER - manifest["format_mm"][0]) < 0.01
                    assert abs(page.rect.height / MILLIMETER - manifest["format_mm"][1]) < 0.01
                    assert page.get_text() == original[index].get_text(), (book["title"], index + 1)
                    assert len(page.get_drawings()) == len(original[index].get_drawings())
                    assert image_hashes(interior, number - 1) == image_hashes(original, index), (
                        number
                    )
                    for font in interior.get_page_fonts(number - 1):
                        assert cast(tuple[str, str, str, bytes], interior.extract_font(font[0]))[
                            3
                        ], (number, font)
                    preview = page.get_pixmap(dpi=150, alpha=False)
                    image = Image.frombytes("RGB", (preview.width, preview.height), preview.samples)
                    bounds = ImageChops.difference(
                        image, Image.new("RGB", image.size, "white")
                    ).getbbox()
                    assert bounds is not None, number
                    left = manifest["gutter_mm"] if number % 2 else manifest["outer_mm"]
                    right = manifest["outer_mm"] if number % 2 else manifest["gutter_mm"]
                    assert bounds[0] >= left * 150 / 25.4 - 2, (number, bounds)
                    assert bounds[2] <= preview.width - right * 150 / 25.4 + 2, (number, bounds)
                    report["pages"].append(
                        {
                            "page": number,
                            "nonwhite_bbox_pixels_150dpi": bounds,
                            "binding_clearance_mm": left if number % 2 else right,
                        }
                    )
    with pymupdf.open(output / "at-the-prompt-review-PROVISIONAL.pdf") as proof:
        assert len(proof) == manifest["proof_pages"] == 138
        for number in (1, 136):
            assert not proof[number].get_text()
            assert not proof[number].get_drawings()
            assert not proof.get_page_images(number)
    with pymupdf.open(output / "at-the-prompt-covers-PROVISIONAL.pdf") as covers:
        assert len(covers) == 4
        for number in (1, 2):
            assert not covers[number].get_text()
            assert not covers[number].get_drawings()
            assert not covers.get_page_images(number)
        for page in covers.pages():
            assert abs(page.rect.width / MILLIMETER - 210) < 0.01
            assert abs(page.rect.height / MILLIMETER - 148) < 0.01
            page.get_pixmap(dpi=150, alpha=False).save(output / f"cover-{page.number + 1}.png")
            for font in covers.get_page_fonts(page.number):
                assert cast(tuple[str, str, str, bytes], covers.extract_font(font[0]))[3]
    (output / "preflight.json").write_text(json.dumps(report, indent=2) + "\n")
    print("132 artwork pages: text, drawing counts, image hashes and embedded fonts preserved.")
    print(
        "134 interior pages, 138 review pages, 4 cover faces (2 blank); binding clearance passed."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("local/proofs"))
    arguments = parser.parse_args()
    preflight(arguments.source, arguments.output)
