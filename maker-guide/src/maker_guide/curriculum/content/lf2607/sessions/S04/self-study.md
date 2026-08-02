# S4 Self-Study Guide: Permissions, Packages, Git

Session: S4

## Study Path

1. Decode `ls -l` before changing permissions.
2. Use `chmod u+x` on one harmless script and verify the owner execute bit.
3. Use `apt search` and `apt show` for discovery only.
4. Initialize git in `~/src`, inspect status, stage source files, and commit.
5. Add `.gitignore` before broad staging so disposable `*.tmp` files stay out of history.
6. Push to Forgejo and verify the remote.

## Permission Decode

```text
-rw-r--r-- 1 username username 12 Aug 1 10:00 hi.txt
| |  |  |
| |  |  others: read only
| |  group: read only
| owner: read and write
regular file
```

Directory execute permission means traversal. Without it, you may see a directory name but cannot enter it.

## Git Minimal Session

```bash
cd ~/src
git status
git config --global user.name "$(whoami)"
git config --global user.email "$(whoami)@kolamayermakers.org"
```

Staged means selected for the next commit. Committed means recorded in history. Pushed means sent to Forgejo.

## Forgejo Remote

Use the `src` repository on the class Forgejo server:

```bash
cd ~/src
git remote add origin "https://lf2607.kolamayermakers.org/git/$(whoami)/src.git"
git remote -v
git push -u origin main
```

If your branch is not named `main`, run `git branch --show-current` and push that branch deliberately.

## Git Recovery

- Missing identity: run `git config --global user.name "$(whoami)"` and `git config --global user.email "$(whoami)@kolamayermakers.org"`, then retry the commit.
- `nothing to commit`: save the file, run `git status`, and check that you are in `~/src`.
- `remote origin already exists`: run `git remote -v`, then use `git remote set-url origin REPO_URL` if the URL is wrong.
- `src refspec main does not match any`: run `git branch --show-current`; push the actual branch or rename it deliberately.
- Scratch file staged: make sure `.gitignore` contains `*.tmp`, remove the scratch file, then run `git status` again before committing.

## Proof Checklist

- You can explain owner, group, and other permissions.
- `~/src/.git` exists.
- `~/src/.gitignore` contains `*.tmp`.
- `git log --oneline` shows at least one source commit.
- `git remote -v` shows `lf2607.kolamayermakers.org/git` and your `src` repository.

## Docs Pointers

- Run `man chmod`, then read symbolic modes.
- Run `git help status`, `git help add`, `git help commit`, and `git help remote`.
- Read the [Pro Git book](https://git-scm.com/book/en/v2) sections on basics and remotes.
- Run `tldr git-status`, `tldr git-commit`, and `tldr git-push`.
- Read [Forgejo Publishing](../../concepts/forgejo-publishing.md) before adding `origin`.
- Read [Permissions](../../concepts/permissions.md) before changing modes outside scratch files.
- Read [Package Management](../../concepts/package-management.md) before asking why learners cannot install packages on the shared server.
- Read [Number Bases: Decimal, Hexadecimal, Octal](../../concepts/number-bases.md) if numeric permissions such as `755` appear.
