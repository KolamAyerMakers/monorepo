# Shell

## Core Idea

A shell is a command interpreter. It reads a line of text, expands shell syntax, starts programs, connects streams, and reports success or failure. Bash is the shell used for this course.

## Command Anatomy

```bash
grep -n ssh /etc/services > ~/playground/matches.txt 2>/dev/null
```

- `grep` is the command name.
- `-n` is an option.
- `ssh` and `/etc/services` are arguments.
- `>` redirects stdout.
- `2>` redirects stderr.
- The shell expands `~` before `grep` starts.

## What The Shell Does Before A Program Runs

1. Reads your line.
2. Splits it into words using shell rules.
3. Expands variables such as `$USER`.
4. Expands `~` and some patterns.
5. Sets up pipes and redirection.
6. Starts the command.
7. Stores the exit status in `$?`.

## Why Quoting Matters

```bash
name='Ada Lovelace'
printf '%s\n' $name
printf '%s\n' "$name"
```

Unquoted variables can split into multiple words. Quoted variables preserve one value. This is why scripts in the course use `"$1"`, `"$HOME"`, and `"$name"`.

## Interactive Shell Versus Script

An interactive shell prints a prompt and waits for you. A script is a file of shell commands run by a shell. The same syntax appears in both, but scripts need more discipline: shebang, `set -euo pipefail`, argument checks, and predictable output.

## Common Confusions

- The shell expands `$HOME`; `ls` receives the expanded path.
- `cd` is a shell builtin because it changes the shell's own current directory.
- `man cd` may not help because some commands are shell builtins; use `help cd` in Bash.
- A command's output is not the same as its exit status.
- `sudo` is not a shell feature and is not part of ordinary learner work on the shared server.

## Proof Check

Run `type cd`, `type grep`, and `type printf`. Explain which are shell builtins and which are external commands on this system.

## Docs Pointers

- Run `man bash`, then read `SHELL GRAMMAR`, `QUOTING`, `REDIRECTION`, and `Pipelines`.
- Run `help`, `help cd`, `help type`, and `help set`.
- Read the [Bash Reference Manual](https://www.gnu.org/software/bash/manual/bash.html).
- Read [Terminal](terminal.md) to separate the shell from the terminal app.
- Read [Readline](readline.md) for Bash prompt movement, editing, completion, and history search keystrokes.
- Read [I/O](io.md), [File Descriptor](file-descriptor.md), and [Signal](signal.md) to understand streams, redirection, and interrupts.
