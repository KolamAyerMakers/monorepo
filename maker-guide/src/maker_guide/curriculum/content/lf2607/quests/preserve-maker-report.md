# Preserve the report script in Git

Quest: preserve-maker-report

## Mission

Put `maker-report.sh` in the source repository and commit it with your normal Git workflow.

## Commands You Will Use

- `git log`


## Steps

1. Run `guide now` so this quest is assigned before you create evidence.
2. Put the executable script at `~/src/scripts/maker-report.sh`.
3. Commit it with your normal Git workflow.
4. Run `guide check`.

## Hints

1. Work inside the existing `~/src` repository from S4. If `git status` says it is not a repository, complete the [S4 Git workflow](../sessions/S04/self-study.md#git-workflow) first, then return here.
2. `git log --oneline -- path` shows commits that contain history for that path.
3. The script keeps its grouped redirect to `~/src/pages/maker-report.md`.
4. Copying rather than moving keeps `~/scripts/maker-report.sh` as a working command, but either workflow can preserve the versioned script.
5. The final script must stay executable, committed, and unchanged from HEAD.

## If Check Fails

If the script is untracked, modified, or staged, finish the commit before checking again.

## Related Reading

- [`cp`](../commands/cp.md)
- [`chmod`](../commands/chmod.md)
- [`git status`](../commands/git-status.md)
- [`git log`](../commands/git-log.md)
- [Git Basics](../concepts/git-basics.md)
