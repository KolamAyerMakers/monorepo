# Count a stream

Quest: count-stream

## Mission

Use a pipeline to count the distinct login shells in `/etc/passwd`.

## Commands You Will Use

- `cut`
- `sort`
- `wc`

This quest also uses pipe syntax. The pipe is shell syntax, not a command card.

## Steps

1. Run `cut -d: -f7 /etc/passwd` to print one login shell per line.
2. Run `cut -d: -f7 /etc/passwd | sort -u` to keep distinct shells.
3. Run `cut -d: -f7 /etc/passwd | sort -u | wc -l` to count them.
4. Ask the guide to check your work.

## Hints

1. `wc -l` counts lines.
2. `sort -u` sorts lines and removes duplicates.
3. Use `cut`, `sort -u`, and `wc -l` in one pipeline.

## If Check Fails

Run the pipeline again, then ask the guide to check it.

## Related Reading

- [wc](../commands/wc.md)
- [cut](../commands/cut.md)
- [sort](../commands/sort.md)
- [pipes](../concepts/pipes.md)
