# Make a file executable

Quest: make-file-executable

## Mission

Create a harmless playground file and make it executable.

## Commands You Will Use

- `touch`
- `chmod`
- `ls -l`

## Steps

1. Run `touch ~/playground/permission-test.txt`.
2. Run `chmod u+x ~/playground/permission-test.txt`.
3. Run `ls -l ~/playground/permission-test.txt` and confirm the owner triplet has `x`.
4. Run `guide check` to check the file and executable bit.

## Hints

1. `chmod u+x` adds execute permission for the owner.
2. `ls -l` should show an `x` in the owner triplet.
3. The file does not need script content yet. S5 teaches shebangs and scripts.

## If Check Fails

Rerun `chmod u+x ~/playground/permission-test.txt`, then check the owner execute bit with `ls -l`.

## Related Reading

- [chmod](../commands/chmod.md)
- [permissions](../concepts/permissions.md)
