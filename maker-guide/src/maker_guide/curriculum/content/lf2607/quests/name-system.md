# Name the system

Quest: name-system

## Mission

Run `cat /etc/os-release` and find the `PRETTY_NAME` value.

## Why This Matters

Linux systems describe themselves through files. You do not need to guess what the server is running. Ask the filesystem.

## Commands You Will Use

- `cat`

## Steps

1. Run `cat /etc/os-release`.
2. Find the line beginning with `PRETTY_NAME=`.
3. Read the value after the equals sign.
4. Answer the guide with that value.

## Hints

1. `cat` prints the file to your terminal.
2. Look for uppercase `PRETTY_NAME`.
3. The useful text is inside the quotes on that line.

## If Check Fails

Open the file again and answer with the distribution name from `PRETTY_NAME`.

## Related Reading

- [cat](../commands/cat.md)
- [reading-files](../concepts/reading-files.md)
