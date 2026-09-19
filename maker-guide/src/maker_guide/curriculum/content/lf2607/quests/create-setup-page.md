# Create a setup page

Quest: create-setup-page

## Mission

Create `~/src/pages/setup.md`, link to it from `index.md`, and rebuild.

## Commands You Will Use

- `micro`
- `build-website`

## Steps

1. Open `~/src/pages/setup.md` in an editor. Create it with a useful heading only if absent; otherwise extend its existing content without overwriting it.
2. Keep or add a link to `setup.html` from `~/src/pages/index.md` and a `[Home](index.html)` link on setup. Preserve existing content and links in both files.
3. Run `build-website`.
4. Confirm `~/public_html/setup.html` contains your setup page.
5. Ask the guide to check the source, link, build command, and output.

## Hints

1. Source Markdown belongs under `~/src/pages/`.
2. Generated HTML belongs under `~/public_html/`.
3. The guide checks the source heading, the `index.md` link, the build command, and the generated page.

## If Check Fails

Confirm the source `setup.md` exists and has a heading, and `index.md` links to `setup.html`. Then rebuild and confirm `setup.html` contains the generated page. Building cannot supply a missing source page.

## Related Reading

- [multi-page-sites](../concepts/multi-page-sites.md)
- [build-website](../commands/build-website.md)
