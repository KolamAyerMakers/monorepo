# systemd timer

## Use

```ini
[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
Persistent=true
```

## What It Does

A systemd timer starts a matching service on a schedule. In this course, the timer and service are user units under `~/.config/systemd/user`.

## Minimal Pair

`site-build.service` does the work:

```ini
[Service]
Type=oneshot
WorkingDirectory=%h/src
ExecStart=/usr/local/bin/npm run build
```

`site-build.timer` schedules it:

```ini
[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
Persistent=true
```

## Lifecycle

```bash
systemctl --user daemon-reload
systemctl --user enable --now site-build.timer
systemctl --user list-timers
systemctl --user start site-build.service
journalctl --user -u site-build.service --no-pager -n 50
```

## Watch Out

Timers trigger services. Debug the service first, then debug the schedule.

## Docs Pointers

- Run `man systemd.timer`.
- Read [systemd timer units](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html).
- Read [automation timers](../concepts/automation-timers.md), [systemd user services](../concepts/systemd-user-services.md), [systemctl](systemctl.md), and [journalctl](journalctl.md).
