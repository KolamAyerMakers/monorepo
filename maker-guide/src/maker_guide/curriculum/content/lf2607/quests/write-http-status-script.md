# Write an HTTP status script

Quest: write-http-status-script

## Mission

Create `~/scripts/status-line.sh` that fetches headers and prints a status line.

## Commands You Will Use

- `curl -I`
- `grep`
- `bash`
- `micro`

## Steps

1. Create `~/scripts/status-line.sh`.
2. Use `curl -I` to fetch headers.
3. Use `grep` to keep the `HTTP` status line.
4. Run the script with `bash`.

## Hints

1. Header responses begin with an HTTP status line.
2. `grep HTTP` is enough for this first version.
3. Save the script before running it.

## If Check Fails

Make sure the script contains `curl -I`, `grep`, and `HTTP`.

## Related Reading

- [curl -I](../commands/curl-head.md)
- [grep](../commands/grep.md)
- [shell scripting](../concepts/shell-scripting.md)
- [HTTP basics](../concepts/http-basics.md)
