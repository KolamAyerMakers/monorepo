# Shell Scripting

## Core Idea

A shell script is a file of commands that Bash can run repeatably.

Like any command, a script returns an exit status. `0` means success. Nonzero means failure. Good scripts print useful text and return the right status.

## Practice Alone

Start with a shebang, add `set -euo pipefail`, then run the script with `bash`.

```bash
bash ~/scripts/hello.sh Ada
printf '%s\n' "$?"
bash ~/scripts/hello.sh
printf '%s\n' "$?"
```

The success path and the failure path should return different statuses.

## Done When

Your script works twice in a row without manual fixes.

It also fails clearly when required input is missing.

## Go Deeper

- [Shebang](shebang.md) explains why the first line chooses the interpreter for direct execution.
- [Script permissions](script-permissions.md) explains why `chmod +x` matters.
- [Environment variables](environment-variables.md) explains the values scripts inherit.
- [exit](../commands/exit.md) explains how scripts report failure deliberately.
- [One-liners](oneliner.md) explains when a short shell program can stay at the prompt.
