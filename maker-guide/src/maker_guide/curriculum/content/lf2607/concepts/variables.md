# Variables

## Core Idea

Variables name values so scripts can reuse them.

Shell assignment has no spaces around `=`:

```bash
name="Ada Lovelace"
printf 'Hello, %s\n' "$name"
```

Quotes matter. `"$name"` preserves the value as one piece of text even when it contains spaces.

## Practice Alone

Capture command output under a descriptive name, then print it:

```bash
today=$(date +%F)
printf 'Today: %s\n' "$today"
```

`$(...)` captures stdout and removes trailing newlines. For inputs supplied to a script, see [script arguments](script-arguments.md); for values passed to child processes, see [environment variables](environment-variables.md).

## Watch Out

- `name = value` is not assignment in the shell.
- `$name` without quotes can split on spaces.
- An unset variable normally expands to empty; `set -u` instead reports an error. A supplied empty value is still a value, so required inputs need explicit validation.

## Done When

You can assign one value and pass it to `printf` without losing its spaces.

## Docs Pointers

- Read [quoting](quoting.md), [environment variables](environment-variables.md), [printf](../commands/printf.md), and [env](../commands/env.md).
