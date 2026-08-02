# Prepare a source handoff

Quest: prepare-source-handoff

## Mission

Write recent git history and status into `~/playground/source-handoff.txt`.

## Commands You Will Use

- `git log`
- `git status`
- `>`
- `cat`

## Steps

1. Run `git log` for your site source.
2. Run `git status`.
3. Save useful output into `~/playground/source-handoff.txt`.
4. Use `cat` to inspect the handoff file.

## Hints

1. A handoff should show what changed and whether the tree is clean.
2. Include either log output or status output.
3. The file should be readable plain text.

## If Check Fails

Recreate `~/playground/source-handoff.txt` with git log or status output.

## Related Reading

- [git log](../commands/git-log.md)
- [git status](../commands/git-status.md)
- [redirection](../commands/redirect.md)
- [git basics](../concepts/git-basics.md)
