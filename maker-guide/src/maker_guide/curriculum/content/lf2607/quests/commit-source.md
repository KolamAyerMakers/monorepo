# Commit your source

Quest: commit-source

## Mission

Review a real source change before staging it, then commit and inspect the history. Preserve source as you improve it, not only at the final handoff.

## Commands You Will Use

- `git status`
- `git diff`
- `git add`
- `git commit`
- `git log`

## Steps

1. Run `cd ~/src`. Stop if it fails; do not run Git in a different directory by accident. If this is not yet a repository, follow the [Git workflow](../sessions/S04/self-study.md#git-workflow) first.
2. Run `git status` and `git diff --staged`. If unrelated changes are already staged, preserve them and ask for help separating the work before committing.
3. Run `git diff` to read unstaged changes. Read new files in your editor too: unstaged diffs do not display untracked file contents.
4. Stage only the intended source paths with `git add --`, followed by those paths. For an edited homepage, use `git add -- pages/index.md`; do not use `git add .`.
5. Run `git diff --staged` again. Inspect the complete staged diff for unintended changes and credentials before proceeding.
6. If the staged changes are correct, commit with a message describing the actual work, such as `git commit -m "Document my web server"`. If nothing changed, do not create an empty commit.
7. Run `git log --oneline` and `git status` to confirm the result. This quest does not require pushing.
8. If you use recorded progress, ask the guide to check your command history. Its observation is not a review of your source or proof of a recoverable handoff.

## Hints

1. Commit source, not generated output under `~/public_html`. Never stage passwords, tokens, or private keys.
2. Read both unstaged and staged diffs before the commit; the complete staged diff determines what will be saved.

## If Check Fails

Run the missing git command, then ask for another check.

## Related Reading

- [git add](../commands/git-add.md)
- [git commit](../commands/git-commit.md)
- [git-basics](../concepts/git-basics.md)
