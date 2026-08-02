# Make a file executable

Quest: make-file-executable

## Mission

Create `~/playground/run-me.sh`, add a Bash shebang, and make it executable.

## Commands You Will Use

- `micro`
- `chmod`
- `ls -l`

## Steps

1. Open `micro ~/playground/run-me.sh`.
2. Put `#!/bin/bash` on the first line.
3. Add one harmless command such as `printf 'running\n'`.
4. Run `chmod u+x ~/playground/run-me.sh`.
5. Run `ls -l ~/playground/run-me.sh` and confirm the owner triplet has `x`.
6. Ask the guide to check the file and executable bit.

## Hints

1. The shebang must be the first line.
2. `chmod u+x` adds execute permission for the owner.
3. `ls -l` should show an `x` in the owner triplet.

## If Check Fails

Fix the first line, rerun `chmod u+x ~/playground/run-me.sh`, and check the owner execute bit with `ls -l`.

## Related Reading

- [chmod](../commands/chmod.md)
- [permissions](../concepts/permissions.md)
