# At the Prompt: provisional production specification

| Item | Value or status |
| :--- | :--- |
| Prototype trim size | 210 × 148 mm, landscape |
| Interior | 134 colour pages, reading order, 67 duplex sheets |
| Editorial order | Terminal → Command Line → Linux → Bash → Git, approved by Philippe Muller |
| Original works | 132 pages, including original covers and credits |
| Course additions | Two pages: approved foreword and contents with reading notes |
| Cover faces | Front, blank second cover, blank third cover, back |
| Quoted interior paper | 100 g/m² woodfree white paper |
| Quoted cover stock | 256 g/m² matte art card, single-side matte lamination |
| Target binding | Wire-O on the 148 mm edge; punching specifications pending |
| Prototype binding margin | 12 mm, mirrored; printer approval required |
| Other prototype margins | At least 5 mm; complete proportional page placement |
| Quoted quantity / price | 13 books, $320 including delivery |
| Colour | Source RGB/ICC colours retained; custom covers use RGB |
| Transparency | Retained; printer workflow compatibility to confirm |
| Added fonts | Liberation Sans/Mono and IBM Plex Mono, embedded |
| Title and prompt symbol | IBM Plex Mono Bold |
| Bleed | Printer requested 3 mm; separate bleed exports prepared in `local/print/` |
| Profile / OutputIntent | No printer-specific profile imposed |
| PDF standard | PDF 1.7, not certified PDF/X |
| Crop marks | Absent; confirm printer requirements |
| Spine | No invented width; no spine for Wire-O |
| Local checks | Full interior render, resource/margin preflight, layout tests |
| Physical proof | Printer offers one sample first, then 12 books; sample approval still pending |
| Compilation permission | Marked resolved by Philippe Muller; no independent correspondence obtained |
| Status | PROVISIONAL: do not release for printing |

The approved foreword replaces the placeholder. Its editable text is in
`foreword.txt`, without em dashes. Build. Break. Repeat. appears below the
signature in Liberation Mono, using darker counterparts of the website's
yellow, teal and lime to retain contrast on light paper.

Both outer covers end with these two lines:

> Linux Foundations · 2026  
> Kolam Ayer Community Club · Singapore

The Community Club is identified as the course location, not as an endorsement.
There is no group identity or personal credit on the back cover. The `$` sits
on the Prompt baseline, with a closer cursor proportioned to the title.

The second and third cover faces are blank as requested. They are the inside
faces of two separate cover boards, not additional sheets. The printer requested
a PDF with 3 mm bleed. Binding clearance, RGB acceptance and file organisation
have not been explicitly confirmed.

## Printer-requested bleed exports

Run `make print` after rebuilding the approved-layout proofs if necessary.
`local/print/at-the-prompt-review-3mm-bleed-PROVISIONAL.pdf` contains all 138
faces. Separate 134-page interior, four-face cover and individual outer-cover
PDFs are available in the same directory.

MediaBox and BleedBox are 216 × 154 mm; TrimBox is 210 × 148 mm with 3 mm bleed
on each side. Existing artwork is translated by 3 mm, not enlarged or cropped.
The ivory background extends through the outer-cover bleed. Interior bleed is
white and inside covers remain blank. Source colours/transparency are retained;
no CMYK conversion, PDF/X certification or crop marks have been added.

The complete, interior and cover bleed PDFs were checked against the existing
proofs for page boxes, text and text geometry, vector counts, image streams,
font streams, bookmarks and blank faces. Outer-cover previews were inspected;
the complete PDF passes `qpdf --check`. Printer acceptance remains required.

## Deadline and sample approval

All 13 books are needed for the graduation ceremony on **24 October 2026**.
The printer clarified 3–5 working days after full payment for the sample, then
up to another five working days for the remaining 12 books. This does not yet
constitute a commitment to the ceremony deadline. Request delivery by 23 October
if possible, and a firm schedule covering sample delivery, approval and final
delivery before proceeding. No payment, file transmission or print approval
has been made by the assistant.

## Questions for the printer, to send only with permission

1. Can you produce A5 landscape with Wire-O on the short edge, 67 sheets of
   approximately 100 g/m² and two 250–300 g/m² covers? Specify punching offsets,
   safe areas for each face, and duplex orientation.
2. What bleed, TrimBox/BleedBox and crop marks do you require?
3. Which ICC profile and PDF standard should be used, including transparency
   handling? Do you prefer correctly profiled RGB or a particular CMYK conversion?
4. Do you need single reading-order interior pages without imposition, separate
   outer-cover files, or a four-face cover PDF with blank inside faces?
5. Confirm stock, opacity, lamination, Wire-O size, quantity and a complete bound
   physical proof. If changing to perfect binding, supply the template and
   confirmed spine thickness before designing a wraparound cover.

The reference pack suggested 3 mm bleed, but this is not an approved printer
requirement. Once confirmed, the SVG ivory background can be extended without
scaling the typography.

## Local working files

- `local/proofs/at-the-prompt-review-PROVISIONAL.pdf`: 138 pages, front, blank
  inside front, interior, blank inside back, back; adjusted bookmarks.
- `local/proofs/at-the-prompt-interior-PROVISIONAL.pdf`: 134 single pages.
- `local/proofs/at-the-prompt-covers-PROVISIONAL.pdf`: four faces in cover order.
- `local/proofs/front.pdf`, `local/proofs/back.pdf`: separate outer faces.
- `local/proofs/at-the-prompt-actual-size-samples-A5.pdf`: ten pages for 100% printing.
- `local/proofs/pagination.json`, `local/proofs/preflight.json`: assembly/check records.
- `local/proofs/rendered/`: interior previews and contact sheets.

These files are organised for printer preparation, but are not yet final files
conforming to the printer's requirements. Reading size and printer specifications
remain to be approved. If a separate physical trial copy cannot be scheduled,
request printer technical preflight, a digital proof and first-copy inspection;
colour, readability and punching risks cannot be eliminated by a digital proof.
