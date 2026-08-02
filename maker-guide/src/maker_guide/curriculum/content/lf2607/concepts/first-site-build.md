# First Site Build

## Core Idea

Your first public page proves the full source-to-output loop works.

```text
Markdown source -> build-website -> generated HTML -> HTTPS URL
```

## Course URL

Your first public page uses this shape:

```text
https://lf2607.kolamayermakers.org/~username/
```

## What To Verify

- Source exists under `~/src/pages`.
- `build-website` finishes without an error.
- Generated HTML exists under `~/public_html`.
- The HTTPS URL returns your page.

## Proof Commands

```bash
test -d ~/src/pages
build-website
test -f ~/public_html/index.html
curl -I https://lf2607.kolamayermakers.org/~username/
```

Replace `username` with your course username in the URL. A `200` status means the web server returned the page path successfully.

## Docs Pointers

- Read [build-website](../commands/build-website.md), [Markdown basics](markdown-basics.md), [filesystem as CMS](filesystem-as-cms.md), and [platform reference](../guides/platform-reference.md).
