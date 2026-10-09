# At the Prompt: production sources

See the [audit](AUDIT.md) and [production specification](PRODUCTION.md).
This directory contains only the purchased Julia Evans anthology and its
production sources. Pending work is tracked in [TODO.md](TODO.md).
Purchased PDFs and derived proofs stay in the Git-ignored `local/` directory.
They must not be distributed to learners or uploaded as CI artifacts.

The editable cover sources are `front.svg` and `back.svg`. They retain the
ivory background and dark green accent from the supplied reference pack.
The title and `$` use IBM Plex Mono Bold, vendored with its license in `fonts/`.
The export loads it through a local Fontconfig configuration, without a global
installation. Install the font or use that configuration when editing the SVG
elsewhere to avoid substitution.

The approved foreword is in `foreword.txt`. `assemble.py` lays it out on one page,
rejects overflow and em dashes, and adds the coloured Build. Break. Repeat.
signature. All project Markdown documentation is maintained in English.

## Rebuild the proof locally

Linux requirements: `uv`, Inkscape, Liberation fonts (`fonts-liberation`), and
Poppler utilities for supplementary inspections. Python dependencies are locked
in `uv.lock`. Run from `graduation/book`:

```bash
make
# Override the default ~/Books/Julia Evans Wizard Zines source directory:
make SOURCE="/path/to/private/purchased/zines"
```

`make` assembles the PDFs and runs local preflight. Outputs default to
`local/proofs`; keep any `OUTPUT` override inside Git-ignored `local/`.
`make preflight` checks existing exports without rebuilding them.

- `assemble.py`: approved reading sources/order, foreword, contents, mirrored
  binding margins, bookmarks, four cover faces and actual-size samples.
- `preflight.py`: page counts, preserved text/vector/image resources, embedded
  fonts, blank inside covers and binding clearances.

Only editable content, assembly/preflight code, its small regression test,
dependency lock and licensed fonts are versioned, alongside these production
documents. One-off audit/comparison tools and their results remain under
`local/`, outside Git. The purchased PDFs must be supplied separately; they are
not bundled, downloaded by these scripts or available to CI.

Production uses the five individual-page reading PDFs, not imposed variants.
Original pages remain PDF objects, with no rasterisation or lossy image
recompression. PNGs are inspection previews only. Inkscape embeds cover fonts;
SVG text stays editable.

The proof has 134 interior pages plus four cover faces: front, blank inside front,
blank inside back, back. In the complete reading proof the interior sits between
the two pairs of cover faces, giving 138 pages. Blank inside cover faces are not
extra interior sheets.

Interior dimensions/margins are configurable, but cover SVGs remain 210 × 148 mm.
A format change requires explicit cover adaptation. The current export is an A5
prototype, not a certified final PDF/X or printer-imposed file.

## Check the scripts without the purchased books

```bash
make check
```

The test creates a blank page in memory and verifies that the entire approved
foreword fits on A5. It reads only the course-authored text and installed fonts,
never purchased files. Test discovery is restricted to `test_assembly.py`.
CI runs lint, typing and this test only; it never runs assembly/preflight or
uploads book artifacts. A CI guard rejects tracked PDFs, renders, HTML/ZIP/JSON
production files and transcripts under `graduation/book`.

Git ignores `local/` and generated/purchased file extensions throughout this
directory, including text extractions except `foreword.txt` and the font license.
Do not force-add private files: ignore rules cannot protect a deliberately
force-added file. Book-specific preflight and printer approvals remain local.
