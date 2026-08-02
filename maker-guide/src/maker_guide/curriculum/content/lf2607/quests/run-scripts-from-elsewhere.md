# Run scripts from elsewhere

Quest: run-scripts-from-elsewhere

## Mission

Change directories, then run one script by absolute path from another location.

## Commands You Will Use

- `pwd`
- `cd`
- `bash`

## Steps

1. Run `pwd` to see where you are.
2. Change to another directory.
3. Run a script with a path such as `bash ~/scripts/hello.sh Ada`.
4. Ask the guide to check your command history.

## Hints

1. The current directory and the script path are separate ideas.
2. `~/scripts/...` works even when you are somewhere else.
3. Run the script after changing directories.

## If Check Fails

Run `pwd`, then `cd`, then a command shaped like `bash ~/scripts/...`.

## Related Reading

- [pwd](../commands/pwd.md)
- [cd](../commands/cd.md)
- [bash](../commands/bash.md)
- [path](../concepts/path.md)
- [shell scripting](../concepts/shell-scripting.md)
