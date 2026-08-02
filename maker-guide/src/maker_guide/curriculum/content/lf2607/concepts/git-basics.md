# Git Basics

## Core Idea

Git records named checkpoints of source files. In this course, commit source under `~/src`; do not treat generated HTML under `~/public_html/` as the source of truth.

The basic loop is:

```text
edit source -> inspect changes -> stage changes -> commit -> push when ready
```

## Practice Alone

Run these from `~/src`:

```bash
git status
git diff
git add pages/index.md
git status
git commit -m "update homepage"
git log --oneline -3
```

Use `git status` before and after staging. It tells you which files are untracked, modified, staged, or clean.

## Common Recovery

- `nothing to commit`: save the file, check that you are in `~/src`, then run `git status` again.
- Missing identity: run `git config --global user.name "$(whoami)"` and `git config --global user.email "$(whoami)@kolamayermakers.org"`, then retry the commit.
- Scratch file appears in status: add a deliberate `.gitignore` rule before broad staging.
- Unsure what changed: run `git diff` before `git add`.

## Done When

You can point to one file and say whether it is unstaged, staged, committed, or pushed.

## Docs Pointers

- Read [git](../commands/git.md), [git status](../commands/git-status.md), [git add](../commands/git-add.md), [git commit](../commands/git-commit.md), and [git log](../commands/git-log.md).
- Read [Forgejo publishing](forgejo-publishing.md) when you are ready to push.
