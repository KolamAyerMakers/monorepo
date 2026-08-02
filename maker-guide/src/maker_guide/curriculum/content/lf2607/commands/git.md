# git

## Core Idea

Git records source history as commits. A commit is a named checkpoint of tracked files.

In this course, git protects `~/src`, not generated output in `~/public_html`.

## Basic Loop

```bash
cd ~/src
git status
git add pages/index.md
git commit -m "Update homepage"
git log --oneline -5
git push
```

## Mental Model

- Working tree: files you are editing.
- Staging area: changes selected for the next commit.
- Commit: recorded checkpoint.
- Remote: another repository, such as Forgejo.

## Common Commands

- [git init](git-init.md): create a repository.
- [git status](git-status.md): inspect state.
- [git add](git-add.md): stage changes.
- [git diff](git-diff.md): inspect changes.
- [git commit](git-commit.md): record a checkpoint.
- [git log](git-log.md): read history.
- [git remote](git-remote.md): inspect or set remote repositories.
- [git push](git-push.md): send commits to Forgejo.
- [git clone](git-clone.md): copy a repository.

## Watch Out

Run `git status` before `git add`, before `git commit`, and before `git push`. Most beginner git mistakes start with not reading status.

## Docs Pointers

- Run `git help status`, `git help add`, `git help commit`, and `git help push`.
- Read [Pro Git](https://git-scm.com/book/en/v2).
- Read [git basics](../concepts/git-basics.md) and [Forgejo publishing](../concepts/forgejo-publishing.md).
