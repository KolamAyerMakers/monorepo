# crontab

## Use

```bash
crontab -l
EDITOR=micro crontab -e
```

## What It Does

`crontab` lists or edits scheduled jobs for your user account. Cron jobs run with a small environment, so use absolute paths.

- `-l`: list your current crontab.
- `-e`: edit your current crontab.

`EDITOR=micro` requests Micro for this one command without changing your normal editor setting. Save with `Ctrl-S`, quit with `Ctrl-Q`. If vim opens instead, Esc, `:q!`, Enter quits without saving.

## Practice

Follow the [cron walkthrough](cron.md#safe-workflow) to back up your table, add and inspect a temporary job, and remove it safely.

## Watch Out

- Do not use `crontab -r` for practice cleanup: it removes the whole crontab. Remove only the exact demo line you added, not other jobs that share its output filename.
- Run `crontab -l` visibly before redirecting its output. `no crontab for ...` is expected for a missing table; investigate other errors rather than hiding them.
- Inspect existing backup files before overwriting them and preserve older copies you need. Never restore an old snapshot blindly over newer jobs.

## Docs Pointers

- Run `man crontab` and `man 5 crontab`.
- Read [cron](cron.md) and [automation timers](../concepts/automation-timers.md).
