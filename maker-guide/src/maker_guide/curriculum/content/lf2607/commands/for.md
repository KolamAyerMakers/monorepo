# for

## Use

```bash
for name in Ada Linus Grace; do
  printf 'hello %s\n' "$name"
done
```

## What It Does

`for` repeats commands for each item in a list.

## Common Forms

Explicit list:

```bash
for name in Ada Linus Grace; do
  printf 'hello %s\n' "$name"
done
```

Brace expansion creates words before the loop starts:

```bash
for number in {1..3}; do
  printf '%s\n' "$number"
done
```

Bash expands `{1..3}` to `1 2 3`, then `for` iterates over those three words.

Globbed files:

```bash
for path in /etc/*.conf; do
  printf '%s\n' "$path"
done
```

## Watch Out

Quote variables inside loops.

With Bash's default settings, an unmatched glob remains literal: a loop over `*.md` may print `*.md` once if no files match. Inspect the input pattern before treating it as a list of real files.

If a loop body grows past a few commands, move it into a script.

## Docs Pointers

- Run `help for`.
- Read [loops](../concepts/loops.md), [quoting](../concepts/quoting.md), [one-liners](../concepts/oneliner.md), and [shell scripting](../concepts/shell-scripting.md).
