# printf

## Use

```bash
printf 'Hello %s\n' "$1"
```

## What It Does

`printf` prints formatted text predictably.

## Format Strings

Print a string with a newline:

```bash
printf '%s\n' "hello makers"
```

Print two strings:

```bash
printf 'name=%s shell=%s\n' "$USER" "$SHELL"
```

Print an integer:

```bash
printf 'count=%d\n' 3
```

Pad a field:

```bash
printf '%-10s %s\n' "status" "ok"
```

Print repeated lines in a loop:

```bash
for number in {1..3}; do
  printf 'number=%s\n' "$number"
done
```

## Why Not Echo In Scripts

`printf` does not add a newline unless you include `\n`, and it handles format strings consistently. `echo` differs across shells.

## Watch Out

Quote variables passed to `printf`. Treat the first argument as the format string, not as arbitrary user input.

## Docs Pointers

- Run `help printf`.
- Read [echo](echo.md), [quoting](../concepts/quoting.md), and [shell scripting](../concepts/shell-scripting.md).
