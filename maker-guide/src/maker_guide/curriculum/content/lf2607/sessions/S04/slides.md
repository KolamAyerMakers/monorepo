# Linux Foundations S4

Session: S4

Permissions, packages, git, Forgejo

<!-- end_slide -->

# Today's Story

You are not alone on the machine.

Permissions are how Linux keeps everyone from stepping on everyone else.

Teacher explains the risk, then learners inspect their own files.

<!-- end_slide -->

# Hands-On Spine

Hands-on now: run these against your own source tree.

```bash
ls -l
chmod u+x script
apt search ascii
cd ~/src
git status
git remote -v
```

<!-- end_slide -->

# Exit Goal

Your site source is versioned, committed, and pushed to Forgejo.
<!-- end_slide -->

# Between-Session Practice Route

Highly recommended after class or for catch-up:

Use the guide throughout class and between sessions: run `guide now` for your current session objective; after you complete it, it shows your current quest. Submit prompted answers with `guide answer 'your answer'`, and run `guide check` after practical work. A passing check records your progress.

1. Read permissions with `ls -l`.
2. Make one script executable with `chmod u+x`.
3. Discover packages with `apt search` and `apt show`.
4. Initialize `~/src` as a git repo.
5. Commit, ignore generated files, and push to Forgejo.

<!-- end_slide -->

# Source, Not Output

Commit Markdown, scripts, and configuration.

Do not commit generated `public_html/` output.
