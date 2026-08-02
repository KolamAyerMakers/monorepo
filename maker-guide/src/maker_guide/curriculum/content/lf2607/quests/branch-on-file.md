# Branch on a file

Quest: branch-on-file

## Mission

Create `~/scripts/exists.sh` that prints different text for existing and missing files.

## Commands You Will Use

- `if`
- `then`
- `else`
- `fi`
- `[[ ]]`
- `printf`
- `bash`
- `micro`

## Steps

1. Create `~/scripts/exists.sh`.
2. Test the first argument with `[[ -e "$1" ]]`.
3. Print `exists` in the `then` branch.
4. Print `missing` in the `else` branch.
5. Ask the guide to check the file.

## Hints

1. `$1` is the path supplied to the script.
2. `-e` tests whether a path exists.
3. The check looks for `if`, `[[ -e ... ]]`, `else`, and `fi`.

## If Check Fails

Rewrite the branch using `if [[ -e "$1" ]]; then ... else ... fi`.

## Related Reading

- [if](../commands/if.md)
- [double brackets](../commands/double-brackets.md)
- [conditionals](../concepts/conditionals.md)
