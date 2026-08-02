# Refresh pipes for Bandit

Quest: refresh-pipes-for-bandit

## Mission

Run one pipeline using `grep`, `sort`, and `uniq`, then redirect errors away.

## Commands You Will Use

- `grep`
- `sort`
- `uniq`
- `2>`

This quest also uses pipe syntax and `/dev/null`, which are shell concepts rather than commands.

## Steps

1. Choose text you can search, such as command history or a source directory.
2. Run a pipeline that includes `grep`, `sort`, and `uniq`.
3. Add `2>/dev/null` where permission errors would distract you.
4. Ask the guide to check command history.

## Hints

1. Bandit rewards calm pipelines.
2. `sort | uniq` removes duplicate adjacent lines after sorting.
3. The check needs both a pipeline and stderr redirection.

## If Check Fails

Run a visible `grep ... | sort | uniq` pipeline and include `2>/dev/null`.

## Related Reading

- [pipes](../concepts/pipes.md)
- [stream redirection](../concepts/stream-redirection.md)
- [`/dev/null`](../concepts/dev-null.md)
- [sort](../commands/sort.md)
- [uniq](../commands/uniq.md)
