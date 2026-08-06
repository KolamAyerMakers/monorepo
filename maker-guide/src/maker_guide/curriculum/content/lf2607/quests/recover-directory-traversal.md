# Recover Directory Traversal

Quest: recover-directory-traversal

## Mission

Remove and restore owner execute permission on an owned directory, then explain why entering it failed.

## Commands You Will Use

- `mkdir`
- `chmod`
- `cd`

## Steps

1. Run `cd ~/playground`.
2. Run `mkdir -p no-enter-demo`.
3. Run `chmod u-x no-enter-demo`.
4. Try `cd no-enter-demo`; it should fail.
5. Run `chmod u+x no-enter-demo`.
6. Run `cd no-enter-demo`; it should now work.
7. Answer the guide: why did the first `cd` fail?

## Hints

1. Directory `x` means traversal, not running a directory as a program.
2. Work only inside `~/playground`.
3. Never remove execute permission from `~`, `~/src`, or `~/.ssh`.

## If Check Fails

Run the remove-and-restore `chmod` commands for `no-enter-demo`, then explain that directory execute permission permits traversal.

## Related Reading

- [chmod](../commands/chmod.md)
- [directory](../concepts/directory.md)
- [permissions](../concepts/permissions.md)
