# Command: `build-website`

## Use

```bash
build-website
```

## What It Does

`build-website` is a Bash alias for the course bootstrap. On its first run, it creates your learner-owned Astro project in `~/src`, installs its pinned dependencies, and makes the initial Git commit. Later runs call that project's `npm run build` command.

Your public page lives at `https://lf2607.kolamayermakers.org/~username/`.

## Source And Output

- Edit source files such as `~/src/pages/index.md`; the Astro layouts and components are visible under `~/src/app`.
- Run `build-website`.
- Inspect generated files such as `~/public_html/index.html`.
- Verify over HTTPS with `curl` or a browser.

Generated output is disposable. If a change matters, put it in source or source configuration. `npm run build` is the full build command; it renders Astro, generates the Codex PDF with Pandoc, and publishes the result.

## Practice

```bash
micro ~/src/pages/index.md
build-website
curl -L https://lf2607.kolamayermakers.org/~username/
```

## Watch Out

Do not hand-edit `~/public_html/index.html` as the permanent fix. The next build can overwrite it.

## Docs Pointers

- Read [Markdown basics](../concepts/markdown-basics.md), [site source ownership](../concepts/site-source-ownership.md), and [HTML on the wire](../concepts/html-on-the-wire.md).
- Read [platform reference](../guides/platform-reference.md) for course hostnames and URL shapes.
