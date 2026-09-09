# Try cron and remove it

Quest: try-cron-and-remove-it

## Mission

Optional practice: create a temporary cron job that appends `date` to `~/cron.log`, then remove only that job. Keep every unrelated cron entry. S9 uses a systemd timer for the required site automation.

## Commands You Will Use

- `cron`
- `crontab`
- `date`
- `>>`
- `>`
- `2>`
- `cat`

## Steps

1. Run `printf '%s\n' "$HOME"` and write down your absolute home path.
2. Run `crontab -l` without hiding errors. Existing jobs or `no crontab for ...` are expected; stop and investigate any other error.
3. Inspect `~/crontab.backup` if it already exists, keeping an older backup elsewhere if needed. Then save the current table with `crontab -l > ~/crontab.backup 2>/dev/null || true`.
4. Run `EDITOR=micro crontab -e`. Preserve existing entries and add the demo line below, replacing `/home/username` with your real home path. Do not duplicate it if it is already there. Save with `Ctrl-S` and quit with `Ctrl-Q`.
5. Run `crontab -l` to inspect the installed table. Wait at least two minute boundaries, then run `cat ~/cron.log` and find new date lines.
6. Use `EDITOR=micro crontab -e` to remove only the exact line you added, identified by `# cron-demo`. Save and quit.
7. Run `crontab -l` visibly again, then `crontab -l > ~/crontab.after 2>/dev/null || true` to save the result.
8. Run `diff -u ~/crontab.backup ~/crontab.after`. Expect no change to unrelated jobs. Do not replace the table blindly if something differs.
9. Ask the guide to check the log and cleanup evidence.

```text
* * * * * date >> /home/username/cron.log 2>&1 # cron-demo
```

The five stars mean every minute. `>>` appends stdout; `2>&1` sends stderr to the same log. The shell comment marks your demo so cleanup does not target someone else's job that happens to mention `cron.log`.

`EDITOR=micro` requests Micro for this invocation of `crontab -e`, without changing your normal editor setting. If vim opens instead, press Esc, type `:q!`, and press Enter to leave without saving.

`crontab -l` exits nonzero when no table exists. `2>/dev/null` hides that message and `|| true` makes the backup/snapshot command succeed anyway, leaving an empty file for an empty table. They also hide real failures, which is why you inspect the visible command first; do not use this pattern to conceal unknown errors.

## Hints

1. Use your real home path in cron, not `~`.
2. Cron has a smaller environment than your shell.
3. Remove this temporary job when evidence exists. Do not remove the required site-build timer or any unrelated cron job.
4. Never use `crontab -r` here: it removes the entire table.

## If Check Fails

First make cleanup safe: inspect `crontab -l` and remove only your marked demo line if it remains. Refresh `~/crontab.after` as above, confirm the demo is absent, and compare with the backup. Other jobs may legitimately mention `cron.log`; leave them alone and show the instructor both snapshots if a check objects. Never install an old backup without reviewing every difference, because that could discard newer unrelated jobs.

## Related Reading

- [cron](../commands/cron.md)
- [crontab](../commands/crontab.md)
- [systemd timer](../commands/systemd-timer.md)
- [automation timers](../concepts/automation-timers.md)
