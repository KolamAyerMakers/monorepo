# S4 Self-Study Guide: Permissions, Git, Forgejo

Session: S4

## Study Path

1. Decode `ls -l` before changing permissions.
2. Use `chmod u+x` on the harmless playground file and verify the owner execute bit.
3. Initialize `~/src` with `git init`, then make the initial source commit.
4. Edit source, inspect `git diff`, stage deliberate files, commit, and inspect the log.
5. Preserve the existing `.gitignore`, add `*.tmp`, and prove `scratch.tmp` is ignored.
6. Create the Forgejo repository with `fj`, add or verify `origin`, push, and compare the web UI with `git log`.

## Permission Decode

```text
-rw-r--r-- 1 username username 0 Aug 8 10:00 permission-demo.txt
| |  |  |
| |  |  other: read only
| |  group: read only
| owner: read and write
regular file
```

The first character is file type. The next nine characters are owner, group, and other permission triplets in the basic Unix permission model.

For a file, `r` reads content, `w` changes content, and `x` permits execution. For a directory, `r` lists names, `w` with `x` changes entries, and `x` permits traversal. Without directory `x`, you may see its name but cannot enter it.

```bash
mkdir -p ~/playground  # Only if the directory is missing
cd ~/playground
touch permission-demo.txt
ls -l permission-demo.txt
chmod u-x permission-demo.txt
chmod u+x permission-demo.txt
ls -l permission-demo.txt
```

Removing then adding `x` guarantees that you see the owner execute bit change. `chmod u+x` changes metadata, not file content. Use numeric modes such as `755` only when you can explain all three triplets.

## Permission Lab

First, observe access Linux denies on the shared server. The first two commands may show metadata; the last two should fail with `Permission denied`. That diagnostic is stderr, as in S3; do not change system paths.

```bash
ls -l /etc/shadow
ls -ld /root
cat /etc/shadow
touch /root/lf2607-permission-demo
```

Then create and recover from a denied traversal attempt in a directory you own:

```bash
cd ~/playground
mkdir -p no-enter-demo
printf 'hello\n' > no-enter-demo/note.txt
chmod u-x no-enter-demo
ls -ld no-enter-demo
cd no-enter-demo
cd ~/playground
chmod u+x no-enter-demo
ls -ld no-enter-demo
cd no-enter-demo
cat note.txt
cd ..
rm no-enter-demo/note.txt
rmdir no-enter-demo
```

The first `cd` should fail because directory `x` permits traversal. Restore `x` before cleanup. Never change permissions on `~`, `~/src`, or `~/.ssh` during this lab.

## Git Workflow

`~/src` contains your site source but starts without Git history. Initialize it on `main` before Git can track its files.

```text
edit source -> inspect -> stage -> commit -> push
working tree    git diff  git add  git commit  git push
```

```bash
cd ~/src
git init
git status
git add --all
git status
git commit -m "Initial site source"
git log --oneline -3
micro pages/index.md
git diff
git add pages/index.md
git commit -m "Update homepage"
git status
```

Staged means selected for the next commit. Committed means recorded locally. Pushed means the commit was sent to Forgejo.

## Ignore Scratch Files

The starter `.gitignore` already contains useful rules. Preserve them and add one new line:

```text
*.tmp
```

```bash
micro ~/src/.gitignore
touch ~/src/scratch.tmp
cd ~/src
git status --short
```

`scratch.tmp` should not appear. Ignore rules affect untracked files, so add the rule before staging scratch files. `~/public_html/` is outside `~/src`, so it does not need an ignore rule there.

`--short` prints one compact line per changed path.

## Create The Forgejo Repository

Create the empty repository with your configured class token:

```bash
cd ~/src
fj --host https://lf2607.kolamayermakers.org/git repo create src
```

Your local source repository already has commits. `fj` creates an empty Forgejo repository so your first push adds that history.

## Forgejo Remote

Use the `src` repository on the class Forgejo server. Inspect before adding `origin`:

```bash
cd ~/src
git remote -v
git remote add origin "https://lf2607.kolamayermakers.org/git/$USER/src.git"
git remote -v
git log --oneline -1
git push -u origin main
```

Run `git remote add` only when `git remote -v` showed no `origin`. If `origin` exists, compare its URL with the course URL before changing it. Open the Forgejo web UI and verify the newest commit message there.

## Git Recovery

- `nothing to commit`: save the file, run `git status`, and check that you are in `~/src`.
- `remote origin already exists`: run `git remote -v`, then ask before changing an existing remote URL.
- `src refspec main does not match any`: run `git log --oneline -1`. You need an initial commit before pushing `main`.
- Push rejected: run `git status` and `git log --oneline -3`. Ask for help with the rejection text.
- Scratch file staged: add `*.tmp` to `.gitignore`, then run `git status` before committing.

## Proof Checklist

- You can explain owner, group, and other permission triplets.
- You can state exactly what `chmod u+x` changes.
- You can explain why `cat /etc/shadow` and entering `no-enter-demo` were denied.
- `git log --oneline` shows your initial source commit and homepage update.
- `~/src/.gitignore` preserves its existing rules and contains `*.tmp`.
- `git status --short` omits `scratch.tmp`.
- `git remote -v` shows your Forgejo `src` repository.
- Forgejo shows the newest local source commit.

## Docs Pointers

- Run `man chmod`, then read symbolic modes.
- Run `git help status`, `git help add`, `git help commit`, and `git help remote`.
- Read the [Pro Git book](https://git-scm.com/book/en/v2) sections on recording changes and remotes.
- Read [Forgejo Publishing](../../concepts/forgejo-publishing.md) before adding `origin`.
- Read [Permissions](../../concepts/permissions.md) before changing modes outside scratch files.
- Read [Number Bases: Decimal, Hexadecimal, Octal](../../concepts/number-bases.md) before using numeric modes such as `755`.
