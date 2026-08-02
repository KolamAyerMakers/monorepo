# Capture your environment

Quest: capture-environment

## Mission

Write selected environment variables to `~/playground/env.txt` and inspect them.

## Commands You Will Use

- `env`
- `grep`
- `>`
- `cat`

## Steps

1. Run `env` and look for `HOME` and `PATH`.
2. Save selected environment output to `~/playground/env.txt`.
3. Use `cat` to inspect the saved file.
4. Ask the guide to check the file.

## Hints

1. `env` prints the process environment.
2. Use `grep` to keep only the lines you care about.
3. The file needs at least `HOME=` or `PATH=`.

## If Check Fails

Recreate `~/playground/env.txt` from `env` output and include `HOME=` or `PATH=`.

## Related Reading

- [env](../commands/env.md)
- [grep](../commands/grep.md)
- [environment variables](../concepts/environment-variables.md)
- [stream redirection](../concepts/stream-redirection.md)
