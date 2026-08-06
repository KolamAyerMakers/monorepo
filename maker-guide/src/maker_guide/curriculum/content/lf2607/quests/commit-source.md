# Commit your source

Quest: commit-source

## Mission

Review a source change before staging it, then commit and inspect the history.

## Commands You Will Use

- `git status`
- `git diff`
- `git add`
- `git commit`
- `git log`

## Steps

1. Run `cd ~/src`.
2. Run `git status`.
3. Run `git diff` to read unstaged changes.
4. Stage the source file with `git add`.
5. Run `git diff --staged` to read what the commit will contain.
6. Commit with `git commit -m "save site source"`.
7. Run `git log --oneline` and `git status`.
8. Ask the guide to check your command history.

## Hints

1. Commit source, not generated output.
2. The guide needs to see both diffs before the commit.

## If Check Fails

Run the missing git command, then ask for another check.

## Related Reading

- [git add](../commands/git-add.md)
- [git commit](../commands/git-commit.md)
- [git-basics](../concepts/git-basics.md)
