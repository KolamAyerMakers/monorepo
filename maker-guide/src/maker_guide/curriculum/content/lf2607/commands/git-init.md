# git init

## Use

```bash
work=$(mktemp -d)
git -C "$work" init -b main
```

## What It Does

`git init` creates a repository. Here, `-C` selects a fresh temporary directory and `-b main` names the initial branch. No commit exists until you stage and commit a file.

## Practice

Follow the [Git card](git.md) to create a file and its first commit.

## Watch Out

Check `pwd` first. Initializing git in the wrong directory creates confusion.

## Docs Pointers

- Read [git](git.md) and [git basics](../concepts/git-basics.md).
- Run `git help init`.
