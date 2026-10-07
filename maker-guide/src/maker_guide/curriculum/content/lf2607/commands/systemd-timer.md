# systemd timer

## Use

```ini
[Timer]
OnCalendar=*-*-* 09:00:00
```

## What It Does

A systemd timer starts a matching service on a schedule. User units live under `~/.config/systemd/user` and are managed with `systemctl --user`, without root access.

## Minimal Pair

This standalone example writes the current date to the journal. Create the directory with `mkdir -p ~/.config/systemd/user`, then create these two files with your editor. Inspect existing files before replacing them.

`~/.config/systemd/user/clock-note.service` does the work:

```ini
[Service]
Type=oneshot
ExecStart=/usr/bin/date
```

`~/.config/systemd/user/clock-note.timer` schedules it:

```ini
[Timer]
OnCalendar=*-*-* 09:00:00

[Install]
WantedBy=timers.target
```

## Lifecycle

```bash
systemctl --user daemon-reload
systemctl --user enable --now clock-note.timer
systemctl --user start clock-note.service
systemctl --user list-timers
journalctl --user -u clock-note.service --no-pager -n 20
```

Find a date line from the manual service run and the timer's next run. A oneshot service normally becomes inactive after it finishes successfully.

For this temporary example, stop future runs when finished:

```bash
systemctl --user disable --now clock-note.timer
```

## Schedule Meaning

`OnCalendar=*-*-* 09:00:00` means daily at 09:00 in the server's local time zone. Calendar events are approximate; ask systemd to explain the next occurrence with `systemd-analyze calendar '*-*-* 09:00:00'`. Interval schedules such as `OnBootSec=5min` and `OnUnitActiveSec=1h` instead count from boot or service activation, not a wall-clock time.

## Watch Out

Timers trigger services. Debug the service first, then the schedule. A timer only runs the command in its service; scheduling a renderer does not also refresh its input data. User timers require the user manager to be running; logout behavior depends on lingering.

## Docs Pointers

- Run `man systemd.timer`.
- Read [systemd timer units](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html).
- Read [automation timers](../concepts/automation-timers.md), [systemd user services](../concepts/systemd-user-services.md), [systemctl](systemctl.md), and [journalctl](journalctl.md).
