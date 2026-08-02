# Write hello.sh

Quest: write-hello-script

## Mission

Create executable `~/scripts/hello.sh` that prints `Hello` plus its first argument.

## Commands You Will Use

- `mkdir`
- `bash`
- `chmod +x`
- `printf`
- `micro`

## Steps

1. Run `mkdir -p ~/scripts`.
2. Create `~/scripts/hello.sh` with a Bash shebang.
3. Use `printf 'Hello %s\n' "$1"` inside the script.
4. Run `chmod +x ~/scripts/hello.sh`.
5. Run it with one argument.
6. Ask the guide to check the file.

## Hints

1. `$1` is the first argument.
2. Quote `$1` when printing it.
3. The file needs a shebang and `$1`.

## If Check Fails

Open the script and make sure it starts with `#!/bin/bash` and uses `$1`.

## Related Reading

- [bash](../commands/bash.md)
- [mkdir](../commands/mkdir.md)
- [printf](../commands/printf.md)
- [script-arguments](../concepts/script-arguments.md)
