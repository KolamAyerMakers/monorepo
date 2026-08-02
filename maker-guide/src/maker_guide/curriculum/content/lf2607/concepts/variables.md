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

Assign a value, print it with `printf`, and inspect environment variables with `env`.

```bash
site_title="My Linux Foundations Site"
printf '%s\n' "$site_title"
env | grep '^HOME='
```

Local variables exist in the current shell. Environment variables are exported to child processes.

```bash
local_only="not exported"
export SHARED_WITH_CHILD="exported"
bash -c 'printf "%s\n" "$SHARED_WITH_CHILD"'
```

## Watch Out

- `name = value` is not assignment in the shell.
- `$name` without quotes can split on spaces.
- Environment variables are process input, not permanent configuration unless you put them in a startup file deliberately.

## Done When

You can tell local variables from environment variables.

## Docs Pointers

- Read [quoting](quoting.md), [environment variables](environment-variables.md), [printf](../commands/printf.md), and [env](../commands/env.md).
