# while

## Use

```bash
while [[ "$count" -gt 0 ]]; do
  printf '%s\n' "$count"
done
```

## What It Does

`while` repeats commands while a test succeeds.

## Practice

Make sure the loop changes something, such as decrementing a count.

## Watch Out

If the condition never changes, the loop never ends.
