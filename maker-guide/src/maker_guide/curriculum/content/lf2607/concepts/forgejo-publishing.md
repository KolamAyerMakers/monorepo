# Forgejo Publishing

## Core Idea

Forgejo is where your source repository becomes visible and reviewable.

For this course, your site source starts in `~/src`. Generated HTML under `~/public_html/` should not be the repository you push. Push the source so someone else can read how your site is built.

## Repository Shape

- Web UI: [lf2607.kolamayermakers.org/git/](https://lf2607.kolamayermakers.org/git/).
- Repository name: `src`.
- Local source path: `~/src`.
- Remote name: `origin`.
- HTTPS remote shape: `https://lf2607.kolamayermakers.org/git/username/src.git`.
- SSH remote shape: `git@lf2607.kolamayermakers.org:username/src.git`.
- Proof command: `git remote -v`.

Use your course username in place of `username`. Forgejo uses the same course identity as Unix and IRC. Use HTTPS first unless the instructor has confirmed your Forgejo SSH key setup.

## Practice Alone

Add a remote, push your commits, then inspect the repository in the web UI.

```bash
cd ~/src
git remote add origin "https://lf2607.kolamayermakers.org/git/$(whoami)/src.git"
git remote -v
git push -u origin main
```

If your branch is not named `main`, run `git branch --show-current` and push the branch you actually committed on.

If `origin` already exists, inspect it before changing it:

```bash
git remote -v
git remote set-url origin "https://lf2607.kolamayermakers.org/git/$(whoami)/src.git"
```

## Done When

Your source can be cloned from Forgejo.

You should be able to answer these checks:

- Which Forgejo repository contains your site source?
- What does `git remote -v` print?
- Does `git log --oneline -1` show the commit you pushed?

## Docs Pointers

- Read [platform reference](../guides/platform-reference.md), [SSH keys](ssh-keys.md), [git remote](../commands/git-remote.md), and [git push](../commands/git-push.md).
