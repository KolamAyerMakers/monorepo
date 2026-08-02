# Conditionals

## Core Idea

Conditionals make scripts choose based on a command result or test result.

## Command Result

```bash
if curl -fsS https://example.org >/dev/null; then
  printf 'up\n'
else
  printf 'down\n'
fi
```

The branch depends on exit status: `0` succeeds, nonzero fails.

## Test Result

```bash
if [[ -e "$path" ]]; then
  printf 'exists\n'
fi
```

Use `[[ ]]` for Bash tests on files, strings, and numbers.

## Done When

You can predict which branch runs before executing the script.

## Docs Pointers

- Read [if](../commands/if.md), [`[[ ]]`](../commands/double-brackets.md), [control flow](control-flow.md), [quoting](quoting.md), and [one-liners](oneliner.md).
