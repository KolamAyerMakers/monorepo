# Log network checks

Quest: log-network-checks

## Mission

Append a dated ping result to `~/playground/network-checks.log`.

## Commands You Will Use

- `date`
- `>>`
- `ping`
- `bash`
- `micro`

## Steps

1. Create a small script or one-liner that runs `date`.
2. Run a short `ping` check.
3. Append the output to `~/playground/network-checks.log`.
4. Ask the guide to check the log.

## Hints

1. `>>` appends without deleting previous lines.
2. A log is useful only if it keeps evidence.
3. The file must not be empty.

## If Check Fails

Append a fresh dated network check to `~/playground/network-checks.log`.

## Related Reading

- [date](../commands/date.md)
- [ping](../commands/ping.md)
- [append redirection](../commands/append-redirection.md)
- [network diagnostics](../concepts/network-diagnostics.md)
