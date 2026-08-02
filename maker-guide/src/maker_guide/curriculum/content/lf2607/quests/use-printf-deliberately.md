# Use printf deliberately

Quest: use-printf-deliberately

## Mission

Modify `~/scripts/hello.sh` to use `printf` instead of `echo`.

## Commands You Will Use

- `micro`
- `printf`
- `bash`

## Steps

1. Open `~/scripts/hello.sh`.
2. Replace any greeting `echo` with `printf`.
3. Run the script with an argument.
4. Ask the guide to check the file.

## Hints

1. `printf` needs a format string.
2. Include `\n` if you want a newline.
3. The check looks for `printf` and `$1`.

## If Check Fails

Rewrite the output line as `printf 'Hello %s\n' "$1"`.

## Related Reading

- [printf](../commands/printf.md)
- [quoting](../concepts/quoting.md)
