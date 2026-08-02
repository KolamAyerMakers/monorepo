# Transform a heading with sed

Quest: transform-heading-with-sed

## Mission

Use one `sed` command to turn `# heading` into `<h1>heading</h1>`.

## Commands You Will Use

- `sed`

## Steps

1. Start with `printf '# heading\n'`.
2. Pipe it into `sed`.
3. Write a substitution that emits `<h1>heading</h1>`.
4. Paste the command to the guide.

## Hints

1. Use `s/from/to/` substitution shape.
2. Capture the heading text or write a simple literal transformation.
3. Your answer needs `sed` and `h1`.

## If Check Fails

Test the command again with `printf '# heading\n'` before answering.

## Related Reading

- [sed](../commands/sed.md)
- [text-transforms](../concepts/text-transforms.md)
