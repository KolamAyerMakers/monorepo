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

Assign a script argument to a descriptive name, then print it.

```bash
report_title="$1"
printf '# %s\n' "$report_title"
```

Variables let one script reuse an input under a readable name. Exporting values to child processes is later exploration.

## Watch Out

- `name = value` is not assignment in the shell.
- `$name` without quotes can split on spaces.
- A variable becomes empty when the input it names is missing; later control flow can detect that case.

## Done When

You can assign one value and pass it to `printf` without losing its spaces.

## Docs Pointers

- Read [quoting](quoting.md), [environment variables](environment-variables.md), [printf](../commands/printf.md), and [env](../commands/env.md).
