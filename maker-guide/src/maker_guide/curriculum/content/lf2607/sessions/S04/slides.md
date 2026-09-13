# Linux Foundations S4

Session: S4

Permissions, Git, Forgejo

<!-- end_slide -->

# Your Page And History

This is a shared Linux server.

Linux permissions control access to files. Git records your project history. Forgejo makes that history reviewable.

Today, use one habit throughout: inspect, choose, change, verify.

<!-- end_slide -->

# A Shared Machine Needs Rules

In the basic Unix permission model, every path has an owner, a group, and permissions.

Linux normally checks one permission triplet for the user asking to use the path:

```text
owner -> group member -> everyone else
```

Your home directory is your workspace, not everybody's workspace.

<!-- end_slide -->

# Read One `ls -l` Row

```text
-rw-r--r-- 1 username groupname 0 Aug 8 10:00 permission-demo.txt
| |  |  |
| |  |  other: read only
| |  group: read only
| owner: read and write
regular file
```

The first `-` means this path is a regular file. A `d` in that position means a directory. The next nine characters are three permission triplets.

<!-- end_slide -->

# `rwx` Depends On The Path

| Permission | Regular file | Directory |
|---|---|---|
| `r` read | Read content | List names |
| `w` write | Change content | With `x`, add, remove, or rename entries |
| `x` execute | Run as a program | Traverse through the directory |

Directory `x` is traversal. Without it, a user may see a directory name but cannot enter it or reach paths inside it.

<!-- end_slide -->

# Read The Owner Triplet

Read the first three permission letters after the file type:

```text
-rw-r-----  notes.txt
 ^^^
 rw- means: owner may read and write, but not execute

drwx------  private/
 ^^^
rwx means: owner may read, write, and traverse this directory

-rwxr-x---  tool
 ^^^ ^^^ ^^^
 rwx  r-x  --- means: owner may do all three, group may read and execute, other users have no access
```

Hands-on now:

```bash
mkdir -p ~/playground  # Only if the directory is missing
cd ~/playground
touch permission-demo.txt
ls -l permission-demo.txt
```

Find the first three permission letters after the initial `-` or `d`.

<!-- end_slide -->

# `chmod` Changes Permission Metadata

`chmod` changes who may read, write, or execute a path. For this lab, read a mode as `[who][change][permission]`.

```text
u+x    owner, add, execute
u-x    owner, remove, execute
```

`u` means owner. `+` adds a permission, `-` removes one, and `x` means execute for a file or traversal for a directory.

<!-- end_slide -->

# Change One Bit And Verify It

Hands-on now: work only on the playground file you own.

```bash
ls -l permission-demo.txt       # Inspect the current mode
chmod u-x permission-demo.txt   # Remove owner execute
chmod u+x permission-demo.txt   # Add owner execute again
ls -l permission-demo.txt       # Verify the final mode
```

The first command tells you whether `x` is already present. Removing then adding it guarantees that you see the owner `x` change. `chmod` did not edit the text inside `permission-demo.txt`.

<!-- end_slide -->

# Feel A Permission Denial

Hands-on now: inspect protected paths, then try two operations Linux should refuse.

```bash
ls -l /etc/shadow  # Inspect protected file metadata
ls -ld /root       # Inspect protected directory metadata
cat /etc/shadow    # Try to read protected content
touch /root/demo   # Try to create a protected file
```

The first two may show metadata. The last two should say `Permission denied`. This diagnostic is written to stderr, as in S3. It is expected evidence, not a command to repeat blindly.

<!-- end_slide -->

# Lock Yourself Out Of A Directory

Hands-on now: make a safe directory you own, then remove only your own traversal permission.

```bash
cd ~/playground
mkdir -p locked               # Create an owned directory
echo hello > locked/note.txt  # Create a file inside it
ls -ld locked                 # Inspect its current mode
chmod u-x locked              # Remove owner traversal
ls -ld locked                 # See the missing x
cd locked                     # Try to enter it
```

`cd` should fail with `Permission denied`. The directory still exists, but you removed the `x` that lets you traverse it.

<!-- end_slide -->

# Restore Access And Clean Up

Hands-on now: restore the same bit, prove access works, then remove only your scratch files.

```bash
cd ~/playground
chmod u+x locked    # Restore owner traversal
ls -ld locked       # See x return
cd locked           # Enter successfully
cat note.txt        # Read the file inside
cd ..               # Leave before cleanup
rm locked/note.txt  # Remove the scratch file
rmdir locked        # Remove the empty scratch directory
```

You created the denial, read the evidence, restored access, and cleaned it up.

Never remove execute permission from `~`, `~/src`, or `~/.ssh`.

<!-- end_slide -->

# Numeric Modes Are A Shorthand

S2 used `700` and `600` for SSH files. One permission triplet has three on-or-off bits. Linux writes that three-bit value as one octal digit:

| Permission shape | Binary bits | Octal digit |
|---|---:|---:|
| `rwx` | `111` | `7` |
| `r-x` | `101` | `5` |

`r` has value `4`, `w` has value `2`, and `x` has value `1`.

| Mode digit | Applies to | Permission shape |
|---:|---|---|
| `7` | Owner | `rwx` |
| `5` | Group | `r-x` |
| `5` | Other | `r-x` |

So `755` means `rwxr-xr-x`. Use `chmod u+x` when changing one deliberate bit. Numeric modes set the full shape at once.

<!-- end_slide -->

# Git Records Local Commits

You edited source in `~/src/pages/` and built generated HTML in `~/public_html/`.

It is okay to lose `~/public_html` as you can always rebuild it.
But if you lose `~/src`, you lose your source.

Git records source history as commits. A commit is a named record of selected source changes. Git works locally in `~/src`; Forgejo comes later when you share commits.

<!-- end_slide -->

# Start A Git Repository

Initialize a Git repository in `~/src` and check its status:

```bash
cd ~/src   # Enter the site source directory
git init   # Start local Git history here
git status # Inspect the new repository
```

`git init` creates the hidden `.git` directory where Git stores this project's history.

<!-- end_slide -->

# Git Has Four Places

```text
working tree -> staging area -> local commits -> remote
    edit          git add       git commit      git push
```

- Working tree: source files you are editing.
- Staging area: exact changes selected for the next commit.
- Commit: a named local history record.
- Remote: another copy of the repository, such as Forgejo, GitHub, or GitLab.

<!-- end_slide -->

# Make Your First Commit

This is your first commit. Use `git status` to confirm that the listed files belong to your site source.

```bash
git status                      # Show pending changes
git add --all                   # Stage all changes for commit
git status                      # Confirm what will be committed
git commit -m "Initial source"  # Create the first commit
```

<!-- end_slide -->

# Ask Git What It Sees

Hands-on now: make one small edit to `~/src/pages/index.md`, save it, then inspect.

```bash
cd ~/src   # Return to the source repository
git status # See which files changed
git diff   # Read the unstaged line changes
```

`git status` names changed and untracked files.

`git diff` shows exact unstaged lines. Read both before choosing what to commit.

<!-- end_slide -->

# Keep Disposable Files Out

`.gitignore` applies only inside this repository.

Preserve its existing rules, then add `*.tmp` on its own line.

```bash
cd ~/src           # Work from the repository root
micro .gitignore   # Add *.tmp on its own line
touch scratch.tmp  # Create a disposable source-side file
git status         # Confirm scratch.tmp is ignored
```

Verify that `scratch.tmp` is absent. Ignore rules hide untracked files, so add the rule before staging scratch files. The `.gitignore` change itself belongs in source history.

<!-- end_slide -->

# Stage Exactly What You Mean

```bash
git add pages/index.md .gitignore # Stage only these two files
git status                        # Confirm the staged file list
git diff --staged                 # Read what the next commit will contain
```

`git add` copies the selected file content into the staging area.
It does not commit or upload anything.

After staging, plain `git diff` shows remaining unstaged changes.

`git diff --staged` shows what the next commit will contain.

<!-- end_slide -->

# Commit The Homepage Update

Record and inspect the homepage update:

```bash
git commit -m "Update homepage"  # Record the selected update
git log --oneline -3             # Read the three newest commits
git status                       # Confirm the working tree is clean
```

The message says why this commit matters. A clean status means your working tree matches the latest local commit.

<!-- end_slide -->

# Create The Remote Repository

Create the empty Forgejo repository from your terminal:

```bash
cd ~/src
fj repo create src
```

`fj` uses your configured class token. Your local repository already has commits, so the remote must start empty for your first push to add that history.

<!-- end_slide -->

# Share With A Remote

Forgejo is this course's remote Git server. A remote is another copy of your repository. `origin` is the conventional local name for its URL.

If `git remote -v` prints nothing, add the course remote:

```bash
# Configure the upstream repository
git remote add origin https://lf2607.kolamayermakers.org/git/$USER/src.git
git remote -v         # Verify its URL
git log --oneline -1  # Confirm a commit exists
# Send main and remember this default remote
git push -u origin main
```

If `origin` already exists, inspect its URL before changing it.

A commit must exist before Git can push it.

Read this as: push local `main` to the remote named `origin`, then remember that relationship for later `git push` commands.

Your class token is configured for HTTPS Git and `fj`. Push commits, not loose files. If authentication fails or the push is rejected, stop and read the message.

<!-- end_slide -->

# Verify In Two Places

```bash
git status           # Confirm there are no uncommitted changes
git log --oneline -1 # Read the newest local commit
git remote -v        # Confirm the Forgejo URL
```

Then open `https://lf2607.kolamayermakers.org/git/<your-username>/src` in a browser. The newest commit message should match your local log.

<!-- end_slide -->

# Exit Goal

Before leaving, you can:

- read owner, group, and other permission triplets;
- predict and verify one `chmod u+x` change;
- explain a denied system access and recover from a denied directory traversal;
- explain working tree, staging area, commit, and remote;
- commit source deliberately, then verify it in Forgejo.

<!-- end_slide -->

# Between-Session Practice

Use `guide now` for the S4 objectives and reinforcement quests.

1. Read and change one permission bit in `~/playground`.
2. Initialize `~/src` on `main`, then make the initial source commit.
3. Review a source diff, stage deliberately, commit, and check status.
4. Add `*.tmp` without replacing existing `.gitignore` rules.
5. Create the Forgejo repository with `fj`, push the commit, and verify it in the web UI.
