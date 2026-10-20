# git push

## Use

Use an existing local repository with a commit and a remote you are authorized to write to. Inspect `git remote -v` and `git branch --show-current` first. This example uses remote `origin` and branch `main`; substitute your actual names.

```bash
git push -u origin main
```

## What It Does

`git push` sends commits to a remote repository.

## Practice

Use `-u origin main` the first time so later `git push` knows the default destination.

## Watch Out

Push commits, not uncommitted files. Run `git status` first.

## Recovery Table

| Symptom | What It Usually Means | Fix |
|---|---|---|
| `src refspec main does not match any` | No local `main` branch or no commits | Inspect `git branch --show-current` and `git log --oneline -1`; push the intended existing branch, not a guessed name. |
| `remote origin already exists` | The remote name is already configured | Run `git remote -v`; ask before changing an existing remote. |
| Authentication failed | The Git host rejected your credentials or SSH key | Verify the remote URL and the host's authentication setup before retrying. |
| Push rejected | Remote has commits your local branch does not have | Do not force push. Ask before merging or rebasing. |

## Proof Commands

```bash
git status
```

## Docs Pointers

- Run `git help push`.
- Read [Pro Git: Working with Remotes](https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes).
