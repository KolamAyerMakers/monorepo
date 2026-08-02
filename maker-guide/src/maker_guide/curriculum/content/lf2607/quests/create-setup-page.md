# Create a setup page

Quest: create-setup-page

## Mission

Create `~/src/pages/setup.md`, link to it from `index.md`, and rebuild.

## Commands You Will Use

- `micro`
- `build-website`

## Steps

1. Create `~/src/pages/setup.md` with a useful heading.
2. Add a link to `setup.html` from `~/src/pages/index.md`.
3. Run `build-website`.
4. Confirm `~/public_html/setup.html` contains your setup page.
5. Ask the guide to check the source, link, build command, and output.

## Hints

1. Source Markdown belongs under `~/src/pages/`.
2. Generated HTML belongs under `~/public_html/`.
3. The guide checks the source heading, the `index.md` link, the build command, and the generated page.

## If Check Fails

Rebuild and confirm `setup.md` has a heading, `index.md` links to `setup.html`, and `setup.html` contains the generated page.

## Related Reading

- [multi-page-sites](../concepts/multi-page-sites.md)
- [build-website](../commands/build-website.md)
