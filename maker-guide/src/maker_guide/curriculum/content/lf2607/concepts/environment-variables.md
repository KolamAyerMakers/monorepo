# Environment Variables

## Core Idea

Environment variables are name-value strings passed from a parent process to a child process. They are how shells tell programs about context such as home directory, username, editor, locale, and command search paths.

## Commands To Try

```bash
env
printf '%s\n' "$HOME"
printf '%s\n' "$USER"
printf '%s\n' "$PATH"
```

`PATH` is a colon-separated list of directories the shell searches when you type a command name. If a script says `command not found`, `PATH` is one of the first things to inspect.

## Local Variables Versus Environment

```bash
name='Ada'
export name
```

A plain shell variable is available to the shell. An exported variable is passed to child processes.

## Common Confusions

- `$HOME` is not text replacement by the filesystem; the shell expands it before the command runs.
- `~` is also expanded by the shell, but only in specific positions.
- Cron and systemd services often have a smaller environment than your interactive shell.
- Secrets sometimes live in environment variables. Do not paste full `env` output into public chat.

## Proof Check

Run `env | grep '^PATH='`, then use `command -v python3` to prove the shell found `python3` through that search path.

## Docs Pointers

- Run `man env`.
- Run `man bash`, then search for `Environment` and `Shell Variables`.
- Read the [Bash manual on shell parameters](https://www.gnu.org/software/bash/manual/bash.html#Shell-Parameters).
