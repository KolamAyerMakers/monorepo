# git push

## Use

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
| `src refspec main does not match any` | No local `main` branch or no commits | Run `git branch --show-current`, commit first, then push the actual branch. |
| `remote origin already exists` | The remote name is already configured | Run `git remote -v`; use `git remote set-url origin <repo-url>` if wrong. |
| Authentication failed | Forgejo credentials or SSH key are not accepted | Verify the remote URL and key setup before retrying. |
| Push rejected | Remote has commits your local branch does not have | Do not force push. Ask before merging or rebasing. |

## Proof Commands

```bash
git status
```

## Docs Pointers

- Run `git help push`.
- Read [Pro Git: Working with Remotes](https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes).
