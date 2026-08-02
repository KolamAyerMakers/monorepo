# env

## Use

```bash
env
env | grep '^PATH='
```

## What It Does

`env` prints environment variables available to a process.

An environment variable is a name-value string passed from a parent process to a child process. Scripts, cron jobs, and systemd services may not receive the same environment as your interactive shell.

## Practice

Look for `PATH`, `HOME`, and `USER`.

```bash
printf '%s\n' "$HOME"
printf '%s\n' "$USER"
printf '%s\n' "$PATH"
command -v python3
```

`PATH` is the list of directories the shell searches when you type a command name.

## Expected Output

- `HOME` should point at your home directory.
- `USER` should match your handle.
- `PATH` should be colon-separated.
- `command -v python3` should print the path to the Python executable.

## Watch Out

Environment values can contain sensitive data on other systems. Do not paste them blindly.

## Common Failures

- A command works in your shell but not in cron or systemd: use full paths or set the environment explicitly.
- `command not found`: inspect `PATH` and confirm the command exists with `command -v`.
- Variable appears empty: it may be a shell variable that was never exported.

## Docs Pointers

- Run `man env`.
- Run `man bash`, then search for `Environment` and `Shell Variables`.
- Read [Environment Variables](../concepts/environment-variables.md).
