# Schedule site rebuilds

Quest: schedule-site-rebuilds

## Mission

Create a user systemd timer that runs your site build service on a schedule.

## Commands You Will Use

- `mkdir`
- `micro`
- `systemd timer`
- `systemctl --user`
- `systemctl --user list-timers`
- `journalctl --user`

## Before You Start

Read [S09 self-study](../sessions/S09/self-study.md). This quest has two files: a oneshot service that performs the build and a timer that starts that service.

## Files To Create

Create the unit directory:

```bash
mkdir -p ~/.config/systemd/user
```

`~/.config/systemd/user/site-build.service`:

```ini
[Unit]
Description=Build my site

[Service]
Type=oneshot
WorkingDirectory=%h/src
ExecStart=/usr/local/bin/npm run build
```

`~/.config/systemd/user/site-build.timer`:

```ini
[Unit]
Description=Build my site every hour

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
Persistent=true

[Install]
WantedBy=timers.target
```

## Steps

1. Create both unit files.
2. Run `systemctl --user daemon-reload`.
3. Run `systemctl --user enable --now site-build.timer`.
4. Run `systemctl --user list-timers` and find `site-build.timer`.
5. Run `systemctl --user start site-build.service` to trigger one build immediately.
6. Read logs with `journalctl --user -u site-build.service --no-pager -n 50`.
7. Ask the guide to check both unit files.

## Expected Output

`systemctl --user list-timers` should include `site-build.timer`. The journal should show a completed `site-build.service` run or a specific build error you can fix.

## Hints

1. Timers activate services. Debug the service first.
2. Use `--user`; root systemd is not the target.
3. `Persistent=true` catches missed runs after downtime.

## If Check Fails

- `Unit site-build.timer not found`: check the filename and run `systemctl --user daemon-reload`.
- `list-timers` does not show it: run `systemctl --user enable --now site-build.timer` again and read the error.
- Service fails: run `journalctl --user -u site-build.service --no-pager -n 50` and fix the first real error.
- Service fails to start: check the filename, reload user systemd, then read `journalctl --user -u site-build.service --no-pager -n 50`.

## Related Reading

- [systemd timer](../commands/systemd-timer.md)
- [systemctl list-timers](../commands/systemctl-list-timers.md)
- [automation timers](../concepts/automation-timers.md)
- [systemd timer units](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)
- [systemd service units](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
