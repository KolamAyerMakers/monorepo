# Count your home entries

Quest: count-home-entries

## Mission

Run `ls -la ~` and count the entries in your home directory, excluding `.` and `..`.

## Why This Matters

Your home directory is your base on the server. Some important files are hidden dotfiles, so ordinary `ls` does not show the full picture.

## Commands You Will Use

- `ls`

## Steps

1. Run `ls -la ~`.
2. Ignore the entry named `.`.
3. Ignore the entry named `..`.
4. Count every other entry.
5. Answer the guide with the count.

## Hints

1. `-a` means show hidden files too.
2. `.` means the current directory. `..` means the parent directory.
3. Count the names at the end of the listing lines.

## If Check Fails

Run `ls -la ~` again and recount. Do not count the `.` and `..` entries.

## Related Reading

- [ls](../commands/ls.md)
- [filesystem-navigation](../concepts/filesystem-navigation.md)
