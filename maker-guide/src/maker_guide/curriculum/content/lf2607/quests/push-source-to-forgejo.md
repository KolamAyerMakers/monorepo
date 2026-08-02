# Push source to Forgejo

Quest: push-source-to-forgejo

## Mission

Add `origin` for your Forgejo `src` repository and run `git push -u origin main`.

## Commands You Will Use

- `git remote`
- `git push`

## Steps

1. Open [lf2607.kolamayermakers.org/git/](https://lf2607.kolamayermakers.org/git/) and confirm your `src` repository exists.
2. Run `git remote add origin "https://lf2607.kolamayermakers.org/git/$(whoami)/src.git"` from `~/src`.
3. Run `git remote -v`.
4. Run `git log --oneline -1` to confirm you have a commit to push.
5. Run `git push -u origin main`.
6. Ask the guide to check your command history.

## Hints

1. `origin` is a remote name. It is not the server itself.
2. `git remote -v` must show `lf2607.kolamayermakers.org/git` and your `src` repository.
3. Push commits, not uncommitted files. Check `git log --oneline -1` before pushing.

## If Check Fails

- `remote origin already exists`: run `git remote -v`. If the URL is wrong, run `git remote set-url origin <repo-url>`.
- `src refspec main does not match any`: run `git branch --show-current` and `git log --oneline -1`. Commit first, then push the branch you actually have.
- Authentication failed: confirm that you can log in to [lf2607.kolamayermakers.org/git/](https://lf2607.kolamayermakers.org/git/) with your course account before retrying.
- Push rejected: do not force push. Read the rejection and ask before merging remote history.
- No commits pushed: run `git status` and `git log --oneline -3` to prove a commit exists locally.

## Related Reading

- [git remote](../commands/git-remote.md)
- [git push](../commands/git-push.md)
- [forgejo-publishing](../concepts/forgejo-publishing.md)
- [S04 self-study](../sessions/S04/self-study.md)
- [Pro Git: Working with Remotes](https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes)
