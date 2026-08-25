# Preserve the report script in Git

Quest: preserve-maker-report

## Mission

Copy `maker-report.sh` into the source repository, commit it, and save proof that the complete report generator exists in Git history.

## Commands You Will Use

- `mkdir`
- `cp`
- `chmod`
- `git status`
- `git add`
- `git diff`
- `git commit`
- `git log`
- `>`

## Steps

1. Run `guide now` so this quest is assigned before you create evidence.
2. Run `mkdir -p ~/src/scripts`.
3. Copy `~/scripts/maker-report.sh` to `~/src/scripts/maker-report.sh`.
4. Run `chmod u+x ~/src/scripts/maker-report.sh`.
5. Run `cd ~/src`, then inspect with `git status`.
6. Stage only the script with `git add scripts/maker-report.sh`.
7. Inspect with `git diff --staged`, then commit with `git commit -m "Add maker report script"`.
8. Run `git diff --exit-code HEAD -- scripts/maker-report.sh`. A difference is printed; no output means the working copy matches the commit.
9. Run `git status --short scripts/maker-report.sh`. A clean tracked file produces no output; an untracked file starts with `??`.
10. Run `git log --oneline -- scripts/maker-report.sh > ~/playground/maker-report-git.txt`.
11. Inspect the proof file, then run `guide check`.

## Hints

1. Work inside the existing `~/src` repository from S4. If `git status` says it is not a repository, complete the [S4 Git workflow](../sessions/S04/self-study.md#git-workflow) first, then return here.
2. `git log --oneline -- path` shows commits that contain history for that path.
3. The copied script keeps its grouped redirect to `~/src/pages/maker-report.md`.
4. Keep `~/scripts/maker-report.sh` as the working command. The Git copy is a versioned snapshot; copy it again before committing future script changes.
5. The copied final script must stay executable, match `HEAD`, and have a commit row in the saved log.

## If Check Fails

Run `cd ~/src`, then `git status`. If the script is untracked, modified, or staged, finish the commit. Then rerun the exact `git diff --exit-code`, `git status --short`, and `git log` proof commands before checking again.

## Related Reading

- [`cp`](../commands/cp.md)
- [`chmod`](../commands/chmod.md)
- [`git status`](../commands/git-status.md)
- [`git log`](../commands/git-log.md)
- [Git Basics](../concepts/git-basics.md)
