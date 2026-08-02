# Automation Timers

## Core Idea

Timers make repeatable work happen without a human at the keyboard.

Prefer systemd user timers for course automation. Cron is useful to recognize and fine for simple legacy jobs, but timers give better status, logs, and service integration.

## Practice Alone

Use a systemd user timer to trigger a one-shot build service.

Service path: `~/.config/systemd/user/site-build.service`

```ini
[Unit]
Description=Build personal course site

[Service]
Type=oneshot
WorkingDirectory=%h/src
ExecStart=/usr/local/bin/npm run build
```

Timer path: `~/.config/systemd/user/site-build.timer`

```ini
[Unit]
Description=Rebuild personal course site regularly

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
Persistent=true

[Install]
WantedBy=timers.target
```

Proof commands:

```bash
systemctl --user daemon-reload
systemctl --user enable --now site-build.timer
systemctl --user list-timers
systemctl --user start site-build.service
journalctl --user -u site-build.service --no-pager -n 50
```

## Done When

You can list the timer, say when it runs next, manually start the paired service, and read its logs.

## Docs Pointers

- Read [systemd timer](../commands/systemd-timer.md), [systemctl](../commands/systemctl.md), [journalctl](../commands/journalctl.md), and [cron](../commands/cron.md).
- Read [systemd user services](systemd-user-services.md) and [service logs](service-logs.md).
