# Add an argument guard

Quest: add-argument-guard

## Mission

Add an argument check to `~/scripts/hello.sh` before it uses `$1`.

## Commands You Will Use

- `micro`
- `bash`
- `printf`

## Steps

1. Open `~/scripts/hello.sh`.
2. Check `$#` before reading `$1`.
3. Print a usage line with `printf` when no name is supplied.
4. Run the script with and without an argument.

## Hints

1. `$#` is the number of arguments.
2. Usage text should explain the required argument.
3. Test the failure path before asking the guide to check.

## If Check Fails

Make sure the file contains both an argument-count check and usage output.

## Related Reading

- [bash](../commands/bash.md)
- [printf](../commands/printf.md)
- [script arguments](../concepts/script-arguments.md)
- [shell scripting](../concepts/shell-scripting.md)
