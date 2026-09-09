# Automation Timers

## Core Idea

Timers make repeatable work happen without a human at the keyboard.

Systemd user timers provide status, logs, and service integration without root access. Cron is another scheduler, useful to recognize and suitable for simple jobs.

## Timer And Service

The service describes the work. The matching timer describes when to start it. Keep a long-running server service separate from a oneshot job that generates its files.

For example, rebuilding a site renders the source that already exists. It does not collect fresh report data unless the service explicitly runs that collection command too.

## Monotonic Schedule

```ini
[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
```

- `OnBootSec=5min` is relative to boot. If that point is already past when the timer is activated, it can fire immediately.
- `OnUnitActiveSec=1h` is relative to the paired service's last activation, not the next clock hour.
- This is a monotonic schedule, not a calendar schedule. It does not catch up missed calendar runs after downtime.

## Practice Alone

Create the self-contained date-logging pair on the [systemd timer card](../commands/systemd-timer.md). Start its service manually, inspect the journal, and find the timer in `systemctl --user list-timers`. Disable that practice timer when finished.

## Done When

You can list the timer, explain its next run, manually start the paired service, and identify successful output in its logs. Service status alone does not prove the intended result. User timers also depend on the user manager staying available; see [Lingering](lingering.md) for logout behavior.

## Docs Pointers

- Read [systemd timer](../commands/systemd-timer.md), [systemctl](../commands/systemctl.md), [journalctl](../commands/journalctl.md), and [cron](../commands/cron.md).
- Read [systemd user services](systemd-user-services.md) and [service logs](service-logs.md).
