# Original comic book: editorial rules

Track book-specific pending work in this directory's `TODO.md`.

These rules govern `chapters/` and `sample/`, not the separate purchased anthology.

- Audience: Linux beginners recalling core ideas on their own Linux computer.
  Curriculum is a topic map, not a textbook to compress or a classroom setup to
  reproduce. No classroom hostnames, `/docs`, helper scripts or chat channels.
- Explain the useful idea before the joke or caveat. Name the command prominently.
  Render every command and command fragment in monospace, including inline
  mentions, titles, options and footnotes; keep explanatory prose in handwriting.
  Preserve whitespace explicitly in SVG code blocks (`xml:space="preserve"`):
  indent Bash bodies by two spaces, continuations by an additional two, and align
  closing keywords with their opening keywords. Verify indentation in the rendered
  page, not only in the XML source. Keep tabular output's column spacing intact.
  Use factual file labels, not dialogue spoken by files or decorative file legs.
  A short title must still tell a beginner what the page is about. Never replace
  a definition with a slogan, metaphor or unexplained contrast.
- Every page supplies its own context: introduce terms, files and inputs needed
  to understand it. Explain `/` as filesystem root before any root distinction;
  explain hidden filenames directly, not through a lock metaphor. If space runs
  out, cover fewer ideas rather than removing necessary context.
- Composition: the title names the actual concept (pipes, staging area, package
  installation), not just a joke. A memorable phrase may be secondary. Define
  the concept near the title; give the illustrated command visual prominence,
  not a corner of a footer. Explain starting conditions and the visible result.
- One central question per page. Separate unrelated commands (mkdir and touch);
  keep intentional comparisons together (copy versus move, replace versus append).
  Teach the general operation first; a chosen tool or package is an example.
- Drawings must earn their space: show a flow, state change or concrete example.
  Avoid empty slogan pages and decorative personification. Use before/after
  when a command changes state; label exactly which part changed.
- Runnable examples include every needed input (filename, URL, argument) and
  produce the illustrated result under the stated conditions. Label command,
  file contents and output separately. Do not put executable-looking ellipses
  or tool names in place of complete commands. Mark illustrative output clearly.
- Chronology is part of context: show what happened before a pictured state
  (especially Git staging) and order recovery operations correctly. Introduce
  essential terms in visible text, not only SVG accessibility descriptions.
- Keep all text at least 10 mm from page edges. Preserve readable lettering;
  shorten prose, reflow or split pages rather than cramming text into footers.
  Pastel blocks must align with the intended object or text group, with padding.
  No label may collide with a person, arrow, file outline or another label.
- Review the whole book for a reported recurring issue, not just the quoted page.
  Cross-check titles, definitions, code typography, examples, margins and diagrams.
  External stylistic reviews are inspired readings, not claims that named authors
  participated. Tim Urban-inspired composition feedback outranks Julia
  Evans-inspired composition feedback; technical truth and beginner comprehension
  remain mandatory.
- Use ordinary Linux tools, not classroom conveniences such as Micro, tldr,
  tree or build-website. Do not promise that any editor or utility exists on every
  installation. Use nano for beginner editing, after a distro-labelled installation
  page. Explain administrative privilege and show Debian/Ubuntu versus Fedora
  package commands separately. Do not introduce SSH key pairs in these chapters.
- Teach installation, package-name lookup, updates and removal only in Package
  Management. Elsewhere state tool prerequisites and refer to that chapter;
  do not repeat distro installation commands on each tool's page.
- All S01–S08 chapters must work as generic home-Linux references: no supplied
  accounts, preinstalled helper services, preconfigured proxies, assigned ports,
  preconfigured public domains or assumed support person. State tool/install prerequisites.
  Bind demonstration servers to loopback, never silently expose home files or
  depend on classroom firewall rules. Explain systemd availability, user-manager
  scope and logout policy rather than assuming lingering was enabled for learners.
- The book is a visual reference, not a set of exercises. Short, complete examples
  are welcome. Examples that can overwrite or delete data need an explicit warning
  beside the command, not buried in a footer. Define commands before their risks.
- Keep white paper, black readable text/lines, sparse pastel highlights, original
  loose-line drawings and varied human characters. No horn-like pointed hair tufts
  and no single protagonist pasted into every scene: vary hair, glasses, body
  proportions and posture while keeping each person's design coherent. Clear arrowheads; no crossings,
  floating labels or unexplained symbols. Colour must not be required to understand.
- Review every page as both a Linux expert and a first-time reader: what is it
  for, what does each term mean here, do the pictured input/output and labels match,
  are prerequisites present, and is it useful outside class? Inspect rendered pages
  after editing. Keep descriptions and chapter documentation aligned with artwork.
- Organize the book by knowledge and prerequisites, not session order. Sessions
  S01–S08 are only a coverage checklist. The authoritative reading order is
  `chapters/contents.toml`; legacy SVG paths do not determine chapter membership.
- All documentation and book text are English. Purchased material is never loaded
  or reused for this original book; PDFs/previews remain ignored under `local/`.
