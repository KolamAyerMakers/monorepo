# Extract fields with awk

Quest: extract-fields-with-awk

## Mission

Use `awk` to print the first field from each `/etc/passwd` line.

## Commands You Will Use

- `awk`
- `cat`

## Steps

1. Inspect `/etc/passwd` enough to see that fields use `:`.
2. Run `awk -F: '{print $1}' /etc/passwd`.
3. Read the first usernames printed.
4. Answer the guide with the command.

## Hints

1. `-F:` sets the field separator.
2. `$1` is awk's first field, not the shell's first argument.
3. Your answer needs `awk` and `print`.

## If Check Fails

Run the awk command again and paste the exact command, not only the output.

## Related Reading

- [awk](../commands/awk.md)
- [text-transforms](../concepts/text-transforms.md)
