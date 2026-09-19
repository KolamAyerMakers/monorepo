# Command: `build-website`

## Use

```bash
build-website
```

## What It Does

`build-website` is a platform-provided Bash alias, not a standard Linux command. On its first run, it creates your user-owned Astro project in `~/src` and installs its pinned dependencies. Later runs call that project's `npm run build` command.

The platform reference gives the public URL for your account. This command publishes files; it does not start a separate HTTP backend process.

## Source And Output

- Edit source files such as `~/src/pages/index.md`; the Astro layouts and components are visible under `~/src/app`.
- Run `build-website`.
- Inspect generated files such as `~/public_html/index.html`.
- Verify over HTTPS with `curl` or a browser.

Generated output is disposable. If a change matters, put it in source or source configuration. `npm run build` is the full build command; it renders Astro, generates the Codex PDF with Pandoc, and publishes the result.

A build renders existing source; it does not collect fresh report facts. If a page is produced by a data-collection script, run that script successfully before building. For unattended work, collection must preserve the last valid source on failure and return nonzero, and the build must not run after that failure. A systemd unit cannot invoke the interactive `build-website` alias directly; it needs the actual executable and project working directory.

## Practice

Run the alias once to initialize a missing project or build the existing one. Stop on errors and preserve existing source before editing its homepage:

```bash
build-website
micro ~/src/pages/index.md
build-website
test -s ~/public_html/index.html
```

Then visit the public URL from the platform reference and find your actual change. A generated file alone does not prove public delivery.

## Watch Out

Do not hand-edit `~/public_html/index.html` as the permanent fix. The next build can overwrite it.

## Docs Pointers

- Read [Markdown basics](../concepts/markdown-basics.md), [site source ownership](../concepts/site-source-ownership.md), and [HTML on the wire](../concepts/html-on-the-wire.md).
- Read [platform reference](../guides/platform-reference.md) for hostnames and URL shapes.
