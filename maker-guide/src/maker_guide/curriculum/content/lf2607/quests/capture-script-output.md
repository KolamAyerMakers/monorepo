# Capture script output

Quest: capture-script-output

## Mission

Run `info.sh` and redirect its output into `~/playground/info-output.txt`.

## Commands You Will Use

- `bash`
- `>`
- `cat`

## Steps

1. Run your `info.sh` script with `bash`.
2. Redirect its output to `~/playground/info-output.txt`.
3. Use `cat` to inspect the captured output.
4. Ask the guide to check the file.

## Hints

1. The redirection operator writes command output to a file.
2. Re-run the command if the file is empty.
3. Use `cat` before asking for a check.

## If Check Fails

Run the script again and redirect non-empty output into `~/playground/info-output.txt`.

## Related Reading

- [bash](../commands/bash.md)
- [redirection](../commands/redirect.md)
- [shell scripting](../concepts/shell-scripting.md)
- [stream redirection](../concepts/stream-redirection.md)
