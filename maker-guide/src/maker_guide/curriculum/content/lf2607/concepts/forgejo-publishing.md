# Forgejo Publishing

## Core Idea

Forgejo is where your source repository becomes visible and reviewable.

Git commits exist locally until you push them to a remote. Forgejo hosts that remote and provides a web interface. Publish source so another person can inspect or rebuild it; do not include passwords, tokens, or private files.

## Before publishing

You need a local repository with a commit, a Forgejo account, and permission to create/write a remote repository. The [Git card](../commands/git.md) creates a local demo; it needs no account. Classroom credentials and address conventions are in [Platform Reference](../guides/platform-reference.md).

Create an **empty** remote repository using Forgejo's web interface or a configured [fj](../commands/fj.md). Do not initialize its README when you already have local commits. Copy its clone URL from Forgejo; an HTTPS credential setup is different from an SSH-key setup.

## Practice Alone

In your chosen local repository, first inspect the destination and branch:

```bash
git remote -v
git branch --show-current
git log --oneline -1
```

If no `origin` exists, add the URL you copied. Replace `REPOSITORY_URL` before running this; replace `main` if your branch has a different name:

```bash
git remote add origin 'REPOSITORY_URL'
git remote -v
git push -u origin main
```

If `origin` already exists, do not add it again or replace it blindly. Verify that it is your intended destination. Do not force-push to resolve a rejected push.

## Done When

Your source can be cloned from Forgejo.

You should be able to answer these checks:

- Which Forgejo repository contains your site source?
- What does `git remote -v` print?
- Does `git log --oneline -1` show the commit you pushed?

## Docs Pointers

- Read [platform reference](../guides/platform-reference.md), [SSH keys](ssh-keys.md), [git remote](../commands/git-remote.md), and [git push](../commands/git-push.md).
