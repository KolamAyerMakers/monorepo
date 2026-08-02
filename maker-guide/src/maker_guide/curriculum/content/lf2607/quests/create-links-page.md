# Create a links page

Quest: create-links-page

## Mission

Create `~/src/pages/links.md`, link it from `index.md`, and rebuild.

## Commands You Will Use

- `micro`
- `build-website`

## Steps

1. Create `~/src/pages/links.md` with a heading.
2. Add a link to `links.html` from `~/src/pages/index.md`.
3. Run `build-website`.
4. Ask the guide to check the source files.

## Hints

1. Link to the generated `.html` page from Markdown.
2. Edit source under `~/src/pages`, not `~/public_html`.
3. Rebuild after saving both files.

## If Check Fails

Check that `links.md` has a heading and `index.md` mentions `links.html`.

## Related Reading

- [micro](../commands/micro.md)
- [build-website](../commands/build-website.md)
- [multi-page sites](../concepts/multi-page-sites.md)
- [Markdown basics](../concepts/markdown-basics.md)
