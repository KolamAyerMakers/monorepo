# S4 — Permissions and Git

Understand who can access a file, then save deliberate versions of your site source.

**You need:** `~/src` from your first site build. At home, use [Continue at Home](../../guides/continue-at-home.md). Forgejo publishing is a classroom extension; local Git needs no server.

## 1. Read permission triplets

```text
- rw- r-- r--
  owner group other
```

The first character is the file type (`-` for a regular file, `d` for a directory). The next nine characters are three permission triplets.

| Permission | Regular file | Directory |
|---|---|---|
| `r` | Read content | List names |
| `w` | Change content | Change entries, usually together with `x` |
| `x` | Execute | Traverse: enter or access entries |

```bash
mkdir -p ~/playground
cd ~/playground
touch permission-demo.txt
chmod u-x permission-demo.txt
ls -l permission-demo.txt
chmod u+x permission-demo.txt
ls -l permission-demo.txt
```

The owner's triplet gains `x`. `u` means owning user; `+x` adds execute permission. The contents do not change. An execute bit alone does not make empty text a useful program.

## 2. Deny and restore directory access

Use a fresh directory. If `no-enter-demo` already exists, inspect it and restore any previous experiment before continuing.

```bash
cd ~/playground
mkdir no-enter-demo
printf 'hello\n' > no-enter-demo/note.txt
chmod u-x no-enter-demo
ls -ld no-enter-demo
cd no-enter-demo
```

Expect `Permission denied` from `cd`. You own the directory, so Linux uses the owner's triplet; the other triplets do not rescue your missing `x`.

Restore and clean up:

```bash
chmod u+x no-enter-demo
cat no-enter-demo/note.txt
rm -i no-enter-demo/note.txt
rmdir no-enter-demo
```

Answer the removal prompt deliberately. Do not practise on your home, source, or `.ssh` directories. Numeric modes are useful later; first understand [Permissions](../../concepts/permissions.md).

## 3. Make your first source commit

Git records snapshots locally. A remote repository is an optional second copy.

```text
edit → inspect → stage → commit → optionally push
       git diff  git add git commit         git push
```

The classroom configures your Git identity and default branch. **At home**, configure your own identity if you have not already:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Use the name and email you want attached to commits. An email in a publicly pushed commit can be visible to others.

```bash
cd ~/src
git status
```

If this says “not a git repository,” initialize once:

```bash
git init
```

At home use `git init -b main` instead, explicitly choosing the branch. If history already exists, keep it and continue with the next edit. For a fresh repository, inspect `git status` and its untracked files before staging; do not include credentials.

```bash
git add --all
git diff --cached
git commit -m "Initial site source"
git log --oneline -3
```

`git diff --cached` shows exactly what the next commit will contain.

## 4. Save one change

```bash
micro pages/index.md
git diff -- pages/index.md
git add pages/index.md
git diff --cached
git commit -m "Update homepage"
git status
```

Make and save a real edit before inspecting. Commit only if the entire staged diff contains your intended changes. If unrelated work is staged, unstage its exact paths with `git restore --staged PATH`; this keeps the working files.

**Staged** means selected for the next commit. **Committed** means recorded locally. **Pushed** means sent to a remote.

## 5. Ignore scratch files

Preserve existing `.gitignore` rules. Add this line using `micro .gitignore`:

```text
*.tmp
```

```bash
touch scratch.tmp
git status
git diff -- .gitignore
git add .gitignore
git diff --cached
git commit -m "Ignore temporary files"
```

Check that `scratch.tmp` is absent from status and that only your ignore-rule change is staged. Ignore rules affect **untracked** files. If the scratch file was staged but not committed, run `git restore --staged scratch.tmp` first. If already committed, ignoring it does not remove it from history.

`public_html` is outside this repository; do not stage generated output.

## 6. Classroom extension: publish to Forgejo

The classroom configures `fj` and HTTPS Git with your class token. Do not copy that token into a home practice kit.

```bash
cd ~/src
git remote -v
```

If your Forgejo `src` repository does not exist yet, create it:

```bash
fj repo create src
```

**Only if no `origin` exists**, add it:

```bash
git remote add origin "https://lf2607.kolamayermakers.org/git/$USER/src.git"
```

Otherwise compare the existing URL before changing anything. Confirm your branch is `main` and there is at least one commit:

```bash
git branch --show-current
git log --oneline -1
git push -u origin main
```

Open [Forgejo](https://lf2607.kolamayermakers.org/git/) and compare the newest commit message. At home, stop at local commits unless you choose and configure your own Git host.

## Check yourself

- What does directory `x` allow?
- Can you explain the difference between working, staged, committed, and pushed changes?
- Does your log show your source edits and ignore rule?
- Is `scratch.tmp` ignored while the file still exists?

[Answers](../../guides/self-study-answers.md#s4-permissions-and-git). References: [git diff](../../commands/git-diff.md), [git add](../../commands/git-add.md), and [Forgejo Publishing](../../concepts/forgejo-publishing.md).

## If Git refuses

- `nothing to commit`: check the saved file, directory, and `git status`.
- Missing `main` ref: check the branch and `git log`; there may be no commit yet.
- Push rejected: keep the exact error, inspect `git remote -v` and `git status`. Do not force-push; authentication failures and diverged history need different repairs.
