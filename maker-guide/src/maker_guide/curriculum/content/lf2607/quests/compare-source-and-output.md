# Compare source and output

Quest: compare-source-and-output

## Mission

Use `diff` to compare one source Markdown page with generated HTML output.

## Commands You Will Use

- `diff`
- `build-website`

## Steps

1. Run `build-website`.
2. Pick one source page under `~/src/pages`.
3. Compare it with the generated page under `~/public_html` using `diff`.
4. Ask the guide to check your command history.

## Hints

1. Generated HTML is not supposed to match Markdown exactly.
2. The point is to see what changed between source and output.
3. Run both the build and the diff before asking for a check.

## If Check Fails

Run `build-website`, then run a command starting with `diff`.

## Related Reading

- [build-website](../commands/build-website.md)
- [diff](../commands/diff.md)
- [HTML on the wire](../concepts/html-on-the-wire.md)
- [site source ownership](../concepts/site-source-ownership.md)
