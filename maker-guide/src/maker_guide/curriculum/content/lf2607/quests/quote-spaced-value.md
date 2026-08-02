# Quote a spaced value

Quest: quote-spaced-value

## Mission

Create `~/scripts/quote-name.sh` that preserves a name containing a space.

## Commands You Will Use

- `micro`
- `bash`
- `printf`

## Steps

1. Create `~/scripts/quote-name.sh`.
2. Store a value such as `Ada Lovelace` in a variable.
3. Print the variable with `printf` using `"$name"`.
4. Run the script with `bash`.

## Hints

1. Unquoted variables split on spaces.
2. `"$name"` preserves the value as one argument.
3. The script should visibly contain a spaced value.

## If Check Fails

Open the script again and make sure `printf` receives `"$name"`.

## Related Reading

- [bash](../commands/bash.md)
- [printf](../commands/printf.md)
- [quoting](../concepts/quoting.md)
- [variables](../concepts/variables.md)
