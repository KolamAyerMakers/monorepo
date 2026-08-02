# S5 Self-Study Guide: Scripting Begins

Session: S5

## Study Path

1. Put scripts under `~/scripts/`.
2. Learn that every command returns an exit status: `0` means success, nonzero means failure.
3. Start each script with `#!/bin/bash` and `set -euo pipefail` unless a quest tells you otherwise.
4. Run scripts with `bash script.sh` first, then add executable permission when direct execution matters.
5. Use `printf` instead of `echo` for predictable output.
6. Quote variables such as `"$1"` and `"$name"`.
7. Add argument checks before using required arguments.

## Script Template

```bash
#!/bin/bash
set -euo pipefail

if [[ "$#" -lt 1 ]]; then
  printf 'usage: %s NAME\n' "$0" >&2
  exit 1
fi

printf 'Hello %s\n' "$1"
```

`exit 1` ends the script with a failure status because the caller did not provide the required argument.

`-e` stops after failed commands. `-u` catches unset variables. `pipefail` makes pipelines fail when any stage fails.

## Exit Status

Every command returns one status number to the shell. `0` means success. Any nonzero value means failure. The shell stores the most recent status in `$?`.

```bash
true
printf '%s\n' "$?"
false
printf '%s\n' "$?"
```

Scripts use that same rule. A script should return `0` when it did the requested work and nonzero when it cannot.

```bash
bash ~/scripts/hello.sh Ada
printf '%s\n' "$?"
bash ~/scripts/hello.sh
printf '%s\n' "$?"
```

The second run should fail after the argument guard. That failure is useful: it tells the caller the script did not do the requested work.

## Quoting Test

```bash
name='Ada Lovelace'
printf '%s\n' $name
printf '%s\n' "$name"
```

The unquoted version splits on spaces. The quoted version preserves one value.

## Troubleshooting

- `Permission denied`: run `chmod +x script.sh` or run `bash script.sh`.
- `command not found`: use `./script.sh` for a script in the current directory.
- `bad interpreter`: check the first line with `head -n 1 script.sh`; it must be `#!/bin/bash`.
- `unbound variable`: you used `$1` without passing an argument under `set -u`; add an argument guard.
- Output loses spaces: quote the variable.

## Proof Checklist

- `hello.sh` uses `$1` and `printf`.
- `info.sh` runs `whoami`, `date`, and `hostname`.
- `ask-name.sh` uses `read -r`.
- `reverse.sh` prints `$2` before `$1`.
- `practice.md` publishes command-history evidence.
- Your Forgejo remote has received your source history.
- `hello.sh` handles missing arguments with a useful usage message.
- `~/scripts/README.md` documents your script collection.
- You can explain why `exit 1` marks the missing-argument path as failure.
- You can explain why `set -euo pipefail` makes bugs louder.

## Docs Pointers

- Run `man bash`, then search for `Shell Parameters`, `QUOTING`, `EXIT STATUS`, and `set`.
- Run `help read`, `help printf`, and `help set`.
- Read the [Bash Reference Manual](https://www.gnu.org/software/bash/manual/bash.html) sections on shell parameters and quoting.
- Read [Shebang](../../concepts/shebang.md) to understand why `#!/bin/bash` must be the first line.
- Read [Command: `exit`](../../commands/exit.md) before writing custom failure paths.
- Read [Environment Variables](../../concepts/environment-variables.md) before debugging `PATH`, `$HOME`, or service environments.
