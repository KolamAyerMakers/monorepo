# Try cron and remove it

Quest: try-cron-and-remove-it

## Mission

Create a temporary cron job that appends `date` to `~/cron.log`, then remove it.

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
2. Run `crontab -l > ~/crontab.backup 2>/dev/null || true`.
3. Run `EDITOR=micro crontab -e` and add a one-minute job shaped like `* * * * * date >> /home/username/cron.log 2>&1`, replacing `/home/username` with your real home path.
4. Wait for it to run more than once.
5. Confirm `~/cron.log` contains date lines.
6. Remove only that cron line with `EDITOR=micro crontab -e`.
7. Run `crontab -l > ~/crontab.after 2>/dev/null || true` after removal.
8. Ask the guide to check the log file and the saved crontab proof.

## Hints

1. Use your real home path in cron, not `~`.
2. Cron has a smaller environment than your shell.
3. Remove the job when evidence exists. No quest should leave a recurring job behind.

## If Check Fails

First make cleanup safe: run `crontab -l`, remove any line that writes to `cron.log`, and save the cleaned crontab. Then run `crontab -l > ~/crontab.after 2>/dev/null || true` and confirm `~/cron.log` is non-empty while `~/crontab.after` does not contain `cron.log`.

## Related Reading

- [cron](../commands/cron.md)
- [crontab](../commands/crontab.md)
- [systemd timer](../commands/systemd-timer.md)
- [automation timers](../concepts/automation-timers.md)
