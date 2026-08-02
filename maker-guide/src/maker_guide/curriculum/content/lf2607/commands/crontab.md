# crontab

## Use

```bash
crontab -l
EDITOR=micro crontab -e
crontab -l > ~/crontab.after 2>/dev/null || true
```

## What It Does

`crontab` lists or edits scheduled jobs for your user account. Cron jobs run with a small environment, so use absolute paths such as `/home/username/cron.log` rather than `~/cron.log`.

## Practice

Before editing, save a backup:

```bash
crontab -l > ~/crontab.backup 2>/dev/null || true
```

After editing, list the result:

```bash
crontab -l
```

## Watch Out

Do not use `crontab -r` while learning. It removes the whole crontab. Remove only the line you added, then verify with `crontab -l`.

## Docs Pointers

- Run `man crontab` and `man 5 crontab`.
- Read [cron](cron.md) and [automation timers](../concepts/automation-timers.md).
