# Ask for input

Quest: ask-for-input

## Mission

Create `~/scripts/ask-name.sh` that uses `read` and greets the typed name.

## Commands You Will Use

- `read`
- `printf`
- `bash`
- `micro`

## Steps

1. Create `~/scripts/ask-name.sh`.
2. Prompt with `printf 'Name: '`.
3. Read with `read -r name`.
4. Print a greeting with `printf`.
5. Ask the guide to check the file.

## Hints

1. `read` stores input in a variable.
2. `-r` keeps backslashes literal.
3. The file must contain both `read` and `printf`.

## If Check Fails

Add a `read -r name` line and print the variable after reading it.

## Related Reading

- [read](../commands/read.md)
- [standard-input](../concepts/standard-input.md)
