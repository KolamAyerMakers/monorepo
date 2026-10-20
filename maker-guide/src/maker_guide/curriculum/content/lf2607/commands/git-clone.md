# git clone

## Use

```bash
work=$(mktemp -d)
git init --bare "$work/remote.git"
git clone "$work/remote.git" "$work/copy"
git -C "$work/copy" remote -v
```

## What It Does

`git clone` copies a repository into a new directory.

## Practice

The local example needs no network. An empty-repository warning is expected: the bare remote has no commits yet. `remote -v` shows the local remote path.

For a real project, use `git clone 'REPOSITORY_URL' 'NEW_DIRECTORY'`, replacing both placeholders. Cloning retrieves committed files and history, not uncommitted edits or installed dependencies.

## Watch Out

Cloning creates a new directory. Do not clone into the repository you are already using.

## Docs Pointers

- Read [git](git.md) and [Forgejo publishing](../concepts/forgejo-publishing.md).
- Run `git help clone`.
