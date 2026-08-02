# Read both ends of a file

Quest: read-file-ends

## Mission

Use `head -n 5` and `tail -n 5` on `/etc/services`.

## Why This Matters

Large files are not read top to bottom every time. Unix gives you tools for inspecting the beginning or end quickly.

## Commands You Will Use

- `head`
- `tail`

## Steps

1. Run `head -n 5 /etc/services`.
2. Read the five lines shown.
3. Run `tail -n 5 /etc/services`.
4. Read the five lines shown.
5. Ask the guide to check your work.

## Hints

1. `head` shows the start of a file.
2. `tail` shows the end of a file.
3. `-n 5` means show five lines.

## If Check Fails

The guide needs to see both commands exactly: `head -n 5 /etc/services` and `tail -n 5 /etc/services`.

## Related Reading

- [head](../commands/head.md)
- [tail](../commands/tail.md)
- [reading-files](../concepts/reading-files.md)
