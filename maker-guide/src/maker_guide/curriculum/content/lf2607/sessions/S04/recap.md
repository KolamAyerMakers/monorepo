# S4 Recap: Permissions, Git, Forgejo

Session: S4

## Core Idea

Linux is multi-user. Git is durable memory for your source. Forgejo makes that history reviewable.

## Remember

- `ls -l` shows file type, owner, group, other, and permission bits.
- `chmod u+x` adds execute permission only for the owner.
- `Permission denied` is evidence to inspect.
- `git status` tells you what Git sees; `git diff` shows unstaged lines.
- `git add` selects content for the next commit; `git commit` records it locally.
- `git push` sends commits to Forgejo. It does not send uncommitted files.

## Live Core

You have the core milestone when you can explain a permission row, initialize the source repository, commit source changes, and verify them in Forgejo.

## Optional Reinforcement

Use the S4 quests for permissions, Git, and Forgejo practice. The endpoint is source history you can explain, not just a local website. Run `guide now` for the next scored activity; run `guide check` after practical work. A passing check records progress.

## Can You Explain This?

- Which permission triplet belongs to the owner, and what does directory `x` mean?
- Why did Linux deny `cat /etc/shadow` and `cd ~/playground/no-enter-demo`?
- What is the difference between unstaged, staged, committed, and pushed?
- Why should `scratch.tmp` be ignored while `public_html/` needs no rule in `~/src/.gitignore`?
- What URL does `origin` name, and where can you verify its newest commit?

## Keep

Keep your `.gitignore`, source commits, and Forgejo remote. S5 uses execute permission for scripts, and later sessions use this repository to share your work.

## Full Autonomy

Use [S4 Self-Study Guide: Permissions, Git, Forgejo](self-study.md) for permission decoding, Git staging recovery, Forgejo recovery, and package discovery.
