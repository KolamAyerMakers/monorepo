# git config

## Use

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## What It Does

`git config` stores Git settings. These examples set the name and email Git records on future commits from this Unix account.

## Watch Out

`--global` applies the setting to future repositories for this Unix account. It does not change a Forgejo login or repository remote.

## Docs Pointers

- Read [git](git.md) and [git commit](git-commit.md).
- Run `git help config`.
