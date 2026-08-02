# Commit your source

Quest: commit-source

## Mission

Run `git add`, `git commit`, `git log`, and `git status` for your site source.

## Commands You Will Use

- `git add`
- `git commit`
- `git log`
- `git status`

## Steps

1. Run `cd ~/src`.
2. Run `git status`.
3. Stage source files with `git add`.
4. Commit with `git commit -m "save site source"`.
5. Run `git log --oneline` and `git status`.
6. Ask the guide to check your command history.

## Hints

1. Commit source, not generated output.
2. If git asks for identity, run `git config --global user.name "$(whoami)"` and `git config --global user.email "$(whoami)@kolamayermakers.org"`.
3. The guide needs to see add, commit, log, and status.

## If Check Fails

Run the missing git command and ask for another check.

## Related Reading

- [git add](../commands/git-add.md)
- [git commit](../commands/git-commit.md)
- [git-basics](../concepts/git-basics.md)
