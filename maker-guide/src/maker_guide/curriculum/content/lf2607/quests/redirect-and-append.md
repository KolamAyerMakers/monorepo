# Redirect and append

Quest: redirect-and-append

## Mission

Create `~/playground/hi.txt` with `>`, append a second line with `>>`, and print the result.

## Why This Matters

Redirection is powerful because it lets command output become file content. It is also dangerous because `>` replaces. You need to feel the difference early.

## Commands You Will Use

- `echo`
- `>`
- `>>`
- `cat`

## Steps

1. Run `echo "hello makers" > ~/playground/hi.txt`.
2. Run `echo again >> ~/playground/hi.txt`.
3. Run `cat ~/playground/hi.txt`.
4. Confirm that the file has two lines: `hello makers` and `again`.
5. Ask the guide to check the file.

## Hints

1. Use `>` only for the first line.
2. Use `>>` for the second line.
3. If the file only contains `again`, you used `>` the second time.

## If Check Fails

Recreate the file from scratch. First use `>`, then use `>>`.

## Related Reading

- [echo](../commands/echo.md)
- [redirect](../commands/redirect.md)
- [append redirection](../commands/append-redirection.md)
- [cat](../commands/cat.md)
- [file-creation](../concepts/file-creation.md)
