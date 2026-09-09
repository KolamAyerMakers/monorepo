# while

## Use

```bash
count=3
while [[ "$count" -gt 0 ]]; do
  printf '%s\n' "$count"
  count=$((count - 1))
done
```

## What It Does

`while` repeats commands while a test succeeds. `-gt` means numerically greater than, and `$((count - 1))` subtracts one. This example prints `3`, `2`, and `1`, then stops when `count` reaches zero.

## Practice

Change the initial `count=3` to `count=1`, then to `count=0`. Predict the output before running the complete example each time.

## Watch Out

If the condition stays true, the loop never ends. Keep the decrement in this example; use `Ctrl-C` to stop an accidental endless loop.
