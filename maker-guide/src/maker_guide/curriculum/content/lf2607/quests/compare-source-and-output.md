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
3. Compare it with the generated page using the command below.
4. Ask the guide to check your command history.

For the existing homepage:

```bash
diff ~/src/pages/index.md ~/public_html/index.html || [[ $? -eq 1 ]]
```

`diff` returns `0` for identical files, `1` for differences, and a larger status for an error. `||` runs the right-hand test only when diff returns nonzero; `-eq 1` accepts the expected differences without hiding file-reading errors. Read the differences. The guide records the whole successful comparison command.

## Hints

1. Generated HTML is not supposed to match Markdown exactly.
2. The point is to see what changed between source and output.
3. Run both the build and the diff before asking for a check.

## If Check Fails

Run `build-website`, then the complete comparison above. If a file is missing or unreadable, fix that error rather than replacing the status test with `|| true`.

## Related Reading

- [build-website](../commands/build-website.md)
- [diff](../commands/diff.md)
- [HTML on the wire](../concepts/html-on-the-wire.md)
- [site source ownership](../concepts/site-source-ownership.md)
