# cron and crontab

## Use

```bash
EDITOR=micro crontab -e
crontab -l
```

## What It Does

Cron runs commands on a time schedule. `crontab` edits or lists the schedule for your account.

Cron is useful for simple old-school jobs. In this course, prefer systemd user timers for site rebuilds because they have clearer service status, logs, and failure inspection.

## Crontab Shape

```text
* * * * * date >> /home/username/cron.log 2>&1
```

The five time fields are minute, hour, day of month, month, and day of week. Replace `/home/username` with the absolute path printed by `printf '%s\n' "$HOME"`.

## Safe Workflow

```bash
crontab -l > ~/crontab.backup 2>/dev/null || true
EDITOR=micro crontab -e
crontab -l
cat ~/cron.log
```

Remove the temporary line with `EDITOR=micro crontab -e` after proving it ran.

## Why Timers Are Preferred Here

- `systemctl --user list-timers` shows the next run.
- `systemctl --user status NAME.service` shows service state.
- `journalctl --user -u NAME.service` shows logs.
- Timer files live in `~/.config/systemd/user`, so they are easier to review.

## Watch Out

- Do not use `crontab -r` in this course. It removes the whole crontab.
- Cron has a minimal environment. Use absolute paths.
- Cron output can become mail or disappear depending on system setup. Redirect deliberately.

## Docs Pointers

- Run `man crontab` and `man 5 crontab`.
- Read [automation timers](../concepts/automation-timers.md), [systemd timer](systemd-timer.md), [systemctl](systemctl.md), and [journalctl](journalctl.md).
