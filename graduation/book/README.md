# At the Prompt

A printed anthology of five complete Julia Evans zines, with editable outer
covers and an approved foreword. Order: The Secret Rules of the Terminal,
Bite Size Command Line, Bite Size Linux, Bite Size Bash, How Git Works.

Purchased colour reading PDFs must be supplied privately; do not use the imposed
print editions. Purchased works and generated PDFs/previews stay outside Git.
Do not distribute PDFs to students or upload them as CI artifacts.

## Rebuild

Linux requirements: `make`, `uv`, Inkscape and Liberation fonts
(`fonts-liberation`). Run from `graduation/book`:

```bash
make                     # Assemble and preflight; default source: ~/Books/Julia Evans Wizard Zines
make print               # Add 3 mm bleed to existing proofs
# For another source directory:
make SOURCE="/path/to/private/purchased/zines"
```

- Review: `local/proofs/at-the-prompt-review-PROVISIONAL.pdf`.
- Printer: `local/print/at-the-prompt-review-3mm-bleed-PROVISIONAL.pdf`.
- Separate interior/cover PDFs are generated in the same directories.
- `make preflight` checks existing proofs; `make check` runs source-free code
  checks and regression tests. CI never builds or uploads purchased material.

Edit `front.svg`, `back.svg` and `foreword.txt`; then rebuild both exports.
IBM Plex Mono Bold is vendored with its licence in `fonts/`; the local Fontconfig
configuration lets Inkscape embed it without a global installation.
Assembly preserves original PDF artwork without rasterisation or lossy conversion.

## Print specification

- A5 landscape, 210 × 148 mm; Wire-O on the left-hand 148 mm edge.
- 134 interior pages (67 duplex sheets) plus four cover faces, including blank
  inside covers: **138 faces total**.
- 12 mm mirrored binding margin; at least 5 mm other margins.
- 3 mm bleed: 216 × 154 mm MediaBox/BleedBox, 210 × 148 mm TrimBox.
  Artwork is not enlarged; outer-cover ivory extends through bleed.
- Source colours/transparency retained; no crop marks, CMYK conversion or PDF/X
  certification. Existing exports retain provisional filenames.
- Interior: 100 g/m² woodfree white; covers: 256 g/m² matte art card with
  single-side matte lamination.
- Printer confirmed $320 for 13 books, short-edge binding and two free deliveries:
  one physical sample, then 12 books after approval.

The bleed PDF has been sent to the printer. Books are needed for the ceremony
on **24 October 2026**, ideally delivered by 23 October. Sample approval and a
firm delivery commitment remain tracked in [TODO.md](TODO.md).
