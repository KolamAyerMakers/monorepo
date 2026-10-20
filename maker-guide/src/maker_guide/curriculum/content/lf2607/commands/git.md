# git

## Core Idea

Git records selected file changes as commits. It works locally; a server or account is not required.

## Basic Loop

```bash
work=$(mktemp -d)
cd "$work"
git init -b main
git config user.name "Practice User"
git config user.email "practice@example.invalid"
printf 'First note\n' > note.txt
git status
git add note.txt
git diff --staged
git commit -m "Add first note"
git log --oneline -5
```

Run one command at a time and stop on errors. The identity settings apply only to this temporary repository, not your other projects. Expect one commit containing `note.txt`. Edit that file and repeat from `git status` to record a second version.

## Mental Model

- Working tree: files you are editing.
- Staging area: changes selected for the next commit.
- Commit: recorded history.
- Remote: another repository, such as Forgejo.

## Common Commands

- [git init](git-init.md): create a repository.
- [git status](git-status.md): inspect state.
- [git add](git-add.md): stage changes.
- [git diff](git-diff.md): inspect changes.
- [git commit](git-commit.md): record selected changes.
- [git config](git-config.md): set Git preferences.
- [git log](git-log.md): read history.
- [git remote](git-remote.md): inspect or set remote repositories.
- [git push](git-push.md): send commits to Forgejo.
- [git clone](git-clone.md): copy a repository.

## Watch Out

Read `git status` and the diff before staging or committing. Git does not automatically save untracked files, uncommitted edits, or secrets safely. Keep credentials out of the repository. A remote copy is optional; use [git push](git-push.md) only after choosing and checking a destination.

## Docs Pointers

- Run `git help status`, `git help add`, `git help commit`, and `git help push`.
- Read [Pro Git](https://git-scm.com/book/en/v2).
- Read [git basics](../concepts/git-basics.md) and [Forgejo publishing](../concepts/forgejo-publishing.md).
