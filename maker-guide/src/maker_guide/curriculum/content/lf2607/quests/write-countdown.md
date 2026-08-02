# Write a countdown

Quest: write-countdown

## Mission

Create `~/scripts/countdown.sh` with a `while` countdown from 5 to 1.

## Commands You Will Use

- `while`
- `printf`
- `bash`
- `micro`

## Steps

1. Create `~/scripts/countdown.sh`.
2. Set a counter to `5`.
3. Use `while` to print and decrement until the counter reaches zero.
4. Run the script.
5. Ask the guide to check the file.

## Hints

1. `while` repeats while a condition succeeds.
2. The loop must change the counter.
3. The file must contain `while` and `printf`.

## Example Shape

```bash
count=5
while [[ "$count" -gt 0 ]]; do
  printf '%s\n' "$count"
  count=$((count - 1))
done
```

## If Check Fails

- If the loop never stops, press `Ctrl-C` and check that the counter changes inside the loop.
- If the script prints nothing, add `printf '%s\n' "$count"` inside the loop before decrementing.
- If Bash reports a syntax error, check that `do` and `done` are both present.
- If The guide cannot validate it, make sure the file contains both `while` and `printf`.

## Related Reading

- [while](../commands/while.md)
- [control-flow](../concepts/control-flow.md)
- [S06 self-study](../sessions/S06/self-study.md)
