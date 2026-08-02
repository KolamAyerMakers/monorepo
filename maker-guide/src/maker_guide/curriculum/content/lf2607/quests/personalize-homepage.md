# Personalize your homepage

Quest: personalize-homepage

## Mission

Replace the starter heading in `~/src/pages/index.md`, run `build-website`, then check the generated homepage.

## Why This Matters

Editing generated HTML is a trap because the next build can overwrite it. Editing source, rebuilding, and checking output is the repeatable publishing loop.

## Commands You Will Use

- `micro`
- `build-website`
- `cat`

## Steps

1. Open `~/src/pages/index.md` with `micro`.
2. Replace `A Linux site under construction` with any text.
3. Save the source file and quit the editor.
4. Run `build-website`.
5. Run `cat ~/public_html/index.html` and find your new heading.
6. Ask the guide to check the source and generated homepage.

## Hints

1. Edit `~/src/pages/index.md`, not `~/public_html/index.html`.
2. Rebuild after saving the Markdown source.
3. The starter heading must be gone from both source and generated output.

## If Check Fails

Open `~/src/pages/index.md`, replace the starter heading, save, run `build-website`, then check `~/public_html/index.html` again.

## Related Reading

- [micro](../commands/micro.md)
- [build-website](../commands/build-website.md)
- [markdown-basics](../concepts/markdown-basics.md)
- [site-source-ownership](../concepts/site-source-ownership.md)
