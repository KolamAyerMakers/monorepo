# Git Basics

## Core Idea

Git records selected versions of files as commits. Commit source, not merely output that a build can regenerate. A local repository needs neither an online account nor a remote server.

The basic loop is:

```text
edit source -> inspect changes -> stage changes -> commit -> push when ready
```

## Practice Alone

Create the disposable repository on the [Git card](../commands/git.md), which introduces `note.txt` and records a first commit. Edit that note, save it, then run these from that repository:

```bash
git status
git diff
git add note.txt
git status
git diff --staged
git commit -m "Clarify the note"
git log --oneline -3
```

Use `git status` before and after staging. It tells you which files are untracked, modified, staged, or clean.

## Common Recovery

- `nothing to commit`: save the file, check your repository directory, then inspect `git status` and `git diff --staged`.
- Scratch file appears in status: add a deliberate `.gitignore` rule before broad staging.
- Unsure what changed: run `git diff` before `git add`.

## Done When

You can point to one file and say whether it is unstaged, staged, committed, or pushed.

## Docs Pointers

- Read [git](../commands/git.md), [git status](../commands/git-status.md), [git add](../commands/git-add.md), [git commit](../commands/git-commit.md), and [git log](../commands/git-log.md).
- Read [Forgejo publishing](forgejo-publishing.md) when you are ready to push.
