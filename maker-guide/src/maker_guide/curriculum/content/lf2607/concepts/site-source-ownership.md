# Site Source Ownership

## Core Idea

Your site has source and output.

- Source: Markdown and configuration under `~/src/`, especially `~/src/pages/`.
- Output: generated HTML under `~/public_html/`.

Edit source. Rebuild output. If output breaks, rebuild it. If source breaks, fix the source carefully.

## Proof Commands

```bash
test -d ~/src/pages
test -d ~/public_html
build-website
test -f ~/public_html/index.html
```

After rebuilding, compare one source file with one output file:

```bash
ls ~/src/pages/index.md ~/public_html/index.html
```

They are related, not identical. Markdown source is meant for humans. HTML output is meant for the browser.

## Common Failure

- Editing `~/public_html/index.html` directly seems to work, then disappears after the next build.
- Committing `~/public_html/` records generated output instead of source.
- Forgetting `build-website` leaves the public page behind your source edits.

## Done When

You can explain which file you edit, which command rebuilds output, and which generated file the public URL serves.

## Docs Pointers

- Read [build-website](../commands/build-website.md), [first site build](first-site-build.md), and [filesystem as CMS](filesystem-as-cms.md).
