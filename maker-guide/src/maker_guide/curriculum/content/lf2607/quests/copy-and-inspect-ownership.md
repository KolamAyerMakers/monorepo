# Copy and inspect ownership

Quest: copy-and-inspect-ownership

## Mission

Copy `/etc/hostname` to `~/playground/hostname` and inspect it with `ls -l`. The guide checks that the copy is a regular file owned by your Unix account with exactly the same contents as `/etc/hostname`.

## Why This Matters

Copying creates a new file. The source may be system-owned, but the copy you create in your home directory should belong to you. `ls -l` lets you prove it.

## Commands You Will Use

- `cp`
- `ls -l`

## Steps

1. Run `cp /etc/hostname ~/playground/hostname`.
2. Run `ls -l ~/playground/hostname`.
3. Check that the owner column shows your handle.
4. Ask the guide to check your work.

## Hints

1. `cp` takes source first, destination second.
2. In `ls -l`, the owner appears after the link count.
3. The owner should be your handle, because you created the copy.

## If Check Fails

Run `cp /etc/hostname ~/playground/hostname` again, then ask the guide to check your work.

## Related Reading

- [cp](../commands/cp.md)
- [ls -l](../commands/ls-l.md)
- [file-manipulation](../concepts/file-manipulation.md)
