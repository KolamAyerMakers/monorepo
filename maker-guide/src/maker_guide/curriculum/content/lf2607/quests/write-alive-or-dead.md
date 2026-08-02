# Write alive or dead

Quest: write-alive-or-dead

## Mission

Create `~/scripts/alive.sh` that pings `$1` once and prints `alive` or `dead`.

## Commands You Will Use

- `if`
- `then`
- `else`
- `fi`
- `ping`
- `printf`
- `bash`
- `micro`

## Steps

1. Create `~/scripts/alive.sh`.
2. Use `ping -c 1 "$1"` inside an `if` statement.
3. Print `alive` when ping succeeds.
4. Print `dead` when ping fails.
5. Ask the guide to check the file.

## Hints

1. Commands have exit statuses.
2. `if ping ...; then` branches on the ping result.
3. The file must contain `$1`, `ping`, `alive`, and `dead`.

## Example Shape

```bash
#!/bin/bash
set -euo pipefail

if [[ "$#" -lt 1 ]]; then
  printf 'usage: %s HOST\n' "$0" >&2
  exit 1
fi

if ping -c 1 "$1" >/dev/null 2>&1; then
  printf 'alive\n'
else
  printf 'dead\n'
fi
```

## If Check Fails

- If the script exits with `unbound variable`, add the argument-count guard before using `$1`.
- If it prints `dead` for a working website, remember ping can be blocked; try `1.1.1.1` and compare.
- If it hangs, make sure `ping` uses `-c 1`.
- If validation fails, confirm the script contains `$1`, `ping`, `alive`, and `dead`.

## Related Reading

- [ping](../commands/ping.md)
- [network-diagnostics](../concepts/network-diagnostics.md)
- [ip-addressing-basics](../concepts/ip-addressing-basics.md)
