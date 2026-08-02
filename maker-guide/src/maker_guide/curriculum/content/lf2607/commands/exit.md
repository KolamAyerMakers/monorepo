# Command: `exit`

## Use

```bash
exit
exit 1
```

## What It Does

`exit` ends the current shell or script and returns an exit status to its parent process.

In an interactive remote shell, ending the shell also ends that login session. That is a consequence of the shell exiting, not an SSH-specific feature of `exit`.

## Scripts

```bash
if [[ "$#" -lt 1 ]]; then
  printf 'usage: %s NAME\n' "$0" >&2
  exit 1
fi
```

Use `0` for success and nonzero values for failure.

## Docs Pointers

- Run `help exit`.
- Read [control flow](../concepts/control-flow.md), [conditionals](../concepts/conditionals.md), and [shell scripting](../concepts/shell-scripting.md).
