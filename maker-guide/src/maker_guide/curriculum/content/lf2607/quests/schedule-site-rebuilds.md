# Schedule site rebuilds

Quest: schedule-site-rebuilds

## Mission

Create and enable a user systemd timer that rebuilds your existing site.

## Commands You Will Use

- `mkdir`
- `micro`
- `systemd timer`
- `systemctl --user`
- `systemctl --user list-timers`
- `journalctl --user`

## Before You Start

Read [S09 self-study](../sessions/S09/self-study.md). Keep your working `site.service` and `~/bin/site.sh`; the two new files below schedule builds, not a second web server.

The build renders existing `~/src/pages/maker-report.md`. It does not rerun `~/scripts/maker-report.sh` or refresh collected facts. To collect fresh facts, run `~/scripts/maker-report.sh "My Maker Report"` separately before rebuilding.

## Files To Create

Create the unit directory and open each file. Inspect any existing contents before replacing them:

```bash
mkdir -p ~/.config/systemd/user
micro ~/.config/systemd/user/site-build.service
micro ~/.config/systemd/user/site-build.timer
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

[Install]
WantedBy=timers.target
```

## Steps

1. Create both unit files with the contents above.
2. Run `systemctl --user daemon-reload`.
3. Run `systemctl --user enable --now site-build.timer`.
4. Run `systemctl --user start site-build.service` to trigger one build immediately.
5. Run `systemctl --user list-timers` and find `site-build.timer` and its next run.
6. Read logs with `journalctl --user -u site-build.service --no-pager -n 50`.
7. Run `bash ~/scripts/site-check.sh "" maker-report.html` and inspect the actual site/report results.
8. Preserve both units alongside `site.service` using [Prepare a source handoff](prepare-source-handoff.md).
9. Ask the guide to check both active unit files.

## Expected Output

`systemctl --user list-timers` should include `site-build.timer`. The journal should show a completed build; fix any build error before calling it done. A successful oneshot service normally becomes inactive after finishing.

## Hints

1. Timers activate services. Debug the service first.
2. Use `--user`; root systemd is not the target.
3. `%h` is your home directory. This starter's `/usr/local/bin/npm run build` in `~/src` includes prebuild asset syncing and produces the same output as `build-website`.
4. `OnBootSec=5min` is relative to boot and may fire immediately if that time has passed when you enable the timer. `OnUnitActiveSec=1h` is relative to the service's last activation.
5. This is a monotonic schedule, not a calendar schedule. It does not catch up missed calendar runs after downtime.

## If Check Fails

- `Unit site-build.timer not found`: check the filename and run `systemctl --user daemon-reload`.
- `list-timers` does not show it: run `systemctl --user enable --now site-build.timer` again and read the error.
- Service fails: run `journalctl --user -u site-build.service --no-pager -n 50` and fix the first real error.
- Timer stops after logout: inspect `loginctl show-user "$USER" -p Linger` and bring the output to the instructor, without changing system settings yourself.

## Related Reading

- [systemd timer](../commands/systemd-timer.md)
- [systemctl list-timers](../commands/systemctl-list-timers.md)
- [automation timers](../concepts/automation-timers.md)
- [systemd timer units](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)
- [systemd service units](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
