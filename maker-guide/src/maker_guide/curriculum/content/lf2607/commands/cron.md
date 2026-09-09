# cron and crontab

## Use

```bash
EDITOR=micro crontab -e
crontab -l
```

## What It Does

Cron runs commands on a time schedule. `crontab` edits or lists the schedule for your account.

Cron is useful for simple jobs. Systemd user timers are an alternative with integrated service status, logs, and failure inspection.

## Crontab Shape

```text
* * * * * date >> /home/username/cron.log 2>&1 # cron-demo
```

The five time fields are minute, hour, day of month, month, and day of week. Five stars run every minute. Replace `/home/username` with the absolute path printed by `printf '%s\n' "$HOME"`. `>>` appends output, `2>&1` includes errors, and the shell comment marks this demo for cleanup.

## Safe Workflow

Run `crontab -l` visibly first. A table or `no crontab for ...` is expected; investigate any other error before continuing. Inspect an existing `~/crontab.backup` before replacing it, preserving an older copy separately if needed.

```bash
crontab -l > ~/crontab.backup 2>/dev/null || true
EDITOR=micro crontab -e
crontab -l
```

`EDITOR=micro` requests Micro for that one edit. In Micro, save with `Ctrl-S` and quit with `Ctrl-Q`. Preserve all existing entries and add only the demo line above, without duplicating an existing demo.

`crontab -l` returns nonzero when no table exists. `2>/dev/null` hides the message and `|| true` tolerates that case, producing an empty backup. Both can also conceal genuine failures, so do not skip the visible inspection first.

Wait for two minute boundaries, then run `cat ~/cron.log` to find new date lines. Remove only your marked demo line with `EDITOR=micro crontab -e`, not every line containing `cron.log`. Run `crontab -l` visibly again, then save and compare:

```bash
crontab -l > ~/crontab.after 2>/dev/null || true
diff -u ~/crontab.backup ~/crontab.after
```

Unrelated entries should be unchanged. Inspect differences instead of blindly restoring the whole backup over newer jobs.

## Comparing Timers

- `systemctl --user list-timers` shows the next run.
- `systemctl --user status NAME.service` shows service state.
- `journalctl --user -u NAME.service` shows logs.
- Timer files live in `~/.config/systemd/user`, so they are easier to review.

## Watch Out

- Do not use `crontab -r` for demo cleanup. It removes the whole crontab.
- Cron has a minimal environment. Use absolute paths.
- Cron output can become mail or disappear depending on system setup. Redirect deliberately.

## Docs Pointers

- Run `man crontab` and `man 5 crontab`.
- Read [automation timers](../concepts/automation-timers.md), [systemd timer](systemd-timer.md), [systemctl](systemctl.md), and [journalctl](journalctl.md).
