# At the Prompt: editorial and technical audit

Source audit performed on 2 October 2026. Updated to reflect the approved
foreword, cover changes and blank inside cover faces. This is a local review
proof, not authorised for fabrication.

## Selected sources

Purchase directory: `/home/pmuller/Books/Julia Evans Wizard Zines`.
The three Bite Size reading editions appeared during the initial audit; all five
colour individual-page editions are now available and selected.

| Title | Selected relative path | Individual pages |
| :--- | :--- | ---: |
| Bite Size Command Line | `Bite Size Command Line/Bite Size Command Line - Wizard Zines.pdf` | 24 |
| The Secret Rules of the Terminal | `The Secret Rules of the Terminal/The Secret Rules of the Terminal - Wizard Zines.pdf` | 28 |
| Bite Size Linux | `Bite Size Linux - Wizard Zines.pdf` | 24 |
| Bite Size Bash | `Bite Size Bash - Wizard Zines.pdf` | 28 |
| How Git Works | `How Git Works/How Git Works - Wizard Zines.pdf` | 28 |

All selected editions are 215.9 × 139.7 mm, landscape. They already have the
correct reading order and retain vector illustrations. The choice is based on
geometry, PDF resources and rendered pages, not the reading/print filename.
Assembly imports complete pages without cropping, distortion or rasterisation.

### Available variants

Each print column below exists in colour and black and white. Counts refer to
imposed PDF faces, not individual book pages.

| Title | Colour reading pages | A4 print faces / mm | Letter print faces / mm | Observed imposition |
| :--- | ---: | :--- | :--- | :--- |
| Command Line | 24 | 12 / 297 × 210 | 12 / 279.4 × 215.9 | Two sideways pages, alternating rotation |
| Terminal | 28 | 14 / 210.009 × 297.004 | 14 / 215.9 × 279.4 | Two stacked pages, reversed verso |
| Linux | 24 | 12 / 210.009 × 297.004 | 12 / 215.9 × 279.4 | Two stacked pages, reversed verso |
| Bash | 28 | 14 / 297 × 210 | 14 / 279.4 × 215.9 | Two sideways pages, alternating rotation |
| Git | 28 | 14 / 297.004 × 210.009 | 14 / 279.4 × 215.9 | Two sideways pages, PDF rotation of 90 degrees |

Command Line's four print variants exist both in its own directory and the
Bite Size pack. The inventory retains each path and checksum; compared colour
renders of the duplicate sets match.

The complete inventory contains **47 files, including 40 PDFs**. Per-page
dimensions, rotations, resources and SHA-256 are in `local/audit/inventory.json`;
the readable file table is `local/audit/inventory.md`. Transcripts and print
directions are included. The Downloads cover pack contains two editable SVGs
and production notes, not a binding template or final production PDF.

Outside this collection: Bite Size Networking (24 reading pages, four imposed
12-face variants and a transcript); Git cheat sheet (one 279.4 × 215.9 mm page);
Terminal cheat sheet (two 150.107 × 194.204 mm pages); four one-page Print
Directions files (215.9 × 279.4 mm, matching useful instructions).

### Content, credits and quality

- Each book starts with its original cover, introduction and contents. Main
  material occupies pages 4–22 in Command Line/Linux and 4–26 in the other books.
- Command Line page 23 lists further tools; Linux page 23 recommends further
  reading. Bash, Terminal and Git page 27 contain conclusions and credits.
  Last pages (24 or 28) are original back covers, not disposable blank pages.
- Bite Size lettering consists of vector outlines: crisp at print size, with no
  lettering fonts to embed, but no searchable text. Transcripts were read alongside
  rendered artwork.
- Terminal/Git contain respectively 51/50 TrueType font resources, principally
  `juliabold` and `Inconsolata`, all embedded. Poppler reports no ToUnicode maps
  for these original resources; this affects extraction, not font substitution.
  Assembly preserves the original extractable text.
- Tiny 1 × 1 images often represent solid colours with alpha masks. Some small
  bitmaps reported by MuPDF are interpreted shadows/gradients, not embedded
  illustrations. The inventory distinguishes embedded resources from interpreted
  image appearances.
- Physical-proof watchpoint: Terminal's original front cover contains an
  817 × 538 image at approximately 96 ppi at native size and a 144 ppi mask.
  The colour print edition has no better image. No artificial upsampling was used.
  Git includes solid fills with 144 ppi masks.
- After reconstruction, Terminal/Git pages 2–27 match their Letter colour
  counterparts pixel-for-pixel at 72 ppi. Linux has minimal rendering differences;
  Command Line/Bash have placement, scaling and antialiasing differences. Print
  covers have different margins/treatments, and Bash drawing counts also differ.
  Reading and visual comparison identified no missing or added chapter. This is
  not a claim that variants are binary-identical.
- Black-and-white variants are excluded: they include adapted covers and cannot
  be used to restore the original colour treatment.

## Approved editorial order

Philippe Muller approved the following order and the foreword. The approved text
is included without em dashes, signed with Build. Break. Repeat. in darker print
counterparts of the website colours. Printer specifications remain pending.

1. **The Secret Rules of the Terminal:** establish a map of the terminal and
   explain behaviours already encountered during the course:
   PATH, history, jobs, filenames, redirection, pagers, keyboard behaviour and TTYs.
2. **Bite Size Command Line:** apply that understanding through useful tools,
   from grep and find to ps, less, kill and lsof. Overlap reinforces the terminal
   explanations with concrete commands. Philippe requested Terminal first.
3. **Bite Size Linux:** move from terminal behaviour to the system behind it:
   permissions, /proc, syscalls, signals, descriptors, pipes and sockets. Memory
   and threading chapters open further exploration rather than forming a gate.
4. **Bite Size Bash:** combine commands and system mechanisms into scripts:
   variables, environment, quoting, redirection, conditions, loops, subshells,
   traps and errors. Linux makes the process/pipe/signal explanations less abstract.
5. **How Git Works:** preserve, compare and share scripts and projects. It explains
   commits, branches, merges and remotes for people already puzzled by Git, rather
   than teaching a first command sequence. Its closing invitation to experiment
   in a test repository fits Keep It Going.

Git does not depend on Bash or Linux memory chapters. Its position is editorial:
a continuation for projects, not a technical prerequisite chain.

## Current pagination

| Section | Interior positions | Complete review PDF positions |
| :--- | :--- | :--- |
| Keep It Going | 1 | 3 |
| Contents and reading notes | 2 | 4 |
| Terminal | 3–30 | 5–32 |
| Command Line | 31–54 | 33–56 |
| Linux | 55–78 | 57–80 |
| Bash | 79–106 | 81–108 |
| Git | 107–134 | 109–136 |

**132 original pages + two course pages = 134 interior pages**, or 67 duplex
sheets. The **138-page review PDF** contains front cover at page 1, blank second
cover at page 2, interior at pages 3–136, blank third cover at page 137, and back
cover at page 138. The two blank faces are the inside faces of separate cover
boards, not extra interior sheets.

The redundant title page was removed and reading notes folded into the contents.
No compensation blank was added. Every book starts on a recto, with original
pagination and references unchanged. No global folio is superimposed on artwork;
contents use interior positions and bookmarks follow the actual PDF positions.

Both outer covers identify Linux Foundations · 2026 and Kolam Ayer Community
Club · Singapore as the course and location, without endorsement. The title and
`$` use IBM Plex Mono Bold, with the prompt symbol and cursor arranged together.
The back uses the curiosity-led “There’s more to explore.” copy, with no group
identity or personal credit. Philippe's signature remains in the foreword.

## Format and outstanding approvals

The prototype remains **210 × 148 mm**. Provisional binding margin: **12 mm**,
mirrored left on rectos/right on versos; other minimum margins: **5 mm**.
These are prototype assumptions, not approved punching specifications.
Sources are placed at **89.39%**, giving a 193 × 124.88 mm image-page, centred
vertically and without distortion.

The smallest extractable Git text drops from 6.66 to approximately **5.95 pt**.
Source body text varies, often around 8–11 pt. A5 is therefore a reading prototype,
not an already-approved comfortable format for all ages. **240 × 170 mm** would
allow approximately 103.29% native scale with these margins, about 15.6% larger
than this A5 proof. Size and cost must be approved before changing production.

Print `local/proofs/at-the-prompt-actual-size-samples-A5.pdf` at **100%**, without
fit-to-page or booklet mode. Its ten faces correspond to interior positions
9, 26, 35, 39, 62, 68, 89, 103, 120 and 131. Assess small code examples,
mathematical indices and reading comfort. Assess credit pages, paper, punching
and binding on the complete physical proof before the full run.

### Permission

[Education](https://wizardzines.com/education/),
[FAQ](https://store.wizardzines.com/pages/faq) and
[Print directions](https://wizardzines.com/print/) were consulted on 2 October 2026.
The published teaching permission allows printing and giving copies to students
from a personal-rate purchase, but not distributing the PDFs. It does not
explicitly address compilation under a custom cover with a foreword. Clarification
was marked resolved by Philippe Muller during review. This records his
confirmation, not independently obtained publisher correspondence. No contact
or file transfer has been made by the assistant.

### Checks and limits

- The initial 136-page interior was rendered at 150 ppi and examined through nine
  contact sheets; covers and a dense Git page were also examined at larger scale.
  Sequence, orientation, original covers and joins were coherent, with no apparent
  clipping in the contact sheets.
- The revised 134-page interior has been fully rerendered. Updated covers,
  foreword and contents have been inspected at larger scale. The 132 original
  pages retain their order and recto/verso parity.
- Preflight verifies original extractable text, vector drawing counts, embedded
  image/mask streams and embedded fonts page by page. Rendered binding clearances
  satisfy prototype margins within pixel tolerance. Inside covers are checked blank.
- Main PDFs use PDF 1.7. Updated complete-review and four-face cover exports pass
  `qpdf --check`. Added cover fonts are embedded with ToUnicode maps.
- Source colours and transparency remain intact. No printer ICC profile, PDF/X
  conformance, bleed or crop marks are presumed approved.
- These checks do not replace detailed final inspection at actual size, a target
  press colour proof and a complete bound physical proof.

Outstanding: reading size, printer specifications and stock/binding/quantity.
A separate bound physical proof may not be feasible within the schedule;
request a digital printer proof and first-copy inspection if possible, with
the remaining physical-production risk accepted by Philippe.
