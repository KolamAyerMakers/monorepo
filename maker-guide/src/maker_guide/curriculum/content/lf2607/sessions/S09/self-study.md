# S9 Self-Study: Give Your Website a Daily Update

Session: S9

2026-10-10

## The idea

A systemd timer is the **when**; its matching service is the **what**. A oneshot service runs a finite task and exits. It is separate from the always-running web server. Timers are useful for daily site builds, rotating recommendations, scheduled reminders, and refreshing dashboards.

`OnCalendar=*-*-* 09:00:00` means daily at 09:00 in the server's local time zone. A missing calendar time defaults to midnight. Runs are scheduled with accuracy tolerance, not guaranteed real-time. Check the calendar interpretation with `systemd-analyze calendar '*-*-* 09:00:00'`.

## Build once each morning

Create `~/.config/systemd/user/site-build.service`:

```ini
[Unit]
Description=Build my website

[Service]
Type=oneshot
WorkingDirectory=%h/src
ExecStart=/usr/local/bin/maker-guide-build-personal-website
```

Create `~/.config/systemd/user/site-build.timer`:

```ini
[Unit]
Description=Build my website every morning

[Timer]
OnCalendar=*-*-* 09:00:00

[Install]
WantedBy=timers.target
```

The installed `maker-guide-build-personal-website` helper is the executable behind the classroom's `build-website` shortcut. systemd does not run interactive shell aliases. The build renders existing source; it does not create new content by itself.

Load and test the service before enabling its schedule:

```bash
systemctl --user daemon-reload
systemctl --user start site-build.service
journalctl --user -u site-build.service --no-pager -n 30
```

Resolve errors before scheduling. A successful oneshot normally returns to inactive. Then enable the timer and check its next deadline:

```bash
systemctl --user enable --now site-build.timer
systemctl --user list-timers --all site-build.timer
```

The timer listing is not proof of a successful build; inspect the service journal. User timers need the user manager running. See [lingering](../../concepts/lingering.md) for logout behavior.

## Challenge: a rotating daily pick

Make your site recommend one thing a day: a song, tiny drawing prompt, joke, five-minute game, or local discovery. Create `~/scripts/todays-pick.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

choices=("Draw a robot" "Find a new song" "Photograph a face" "Name a planet" "Recommend a five-minute game" "Make a paper creature" "Share a discovery")
weekday=$(date +%u)
today=$(date +%F)
output="$HOME/src/pages/today.md"
temporary=$(mktemp "$HOME/src/pages/.today.XXXXXX")
trap 'rm -f "$temporary"' EXIT

printf '# Today\x27s Pick\n\n%s\n\n%s\n' "$today" "${choices[weekday - 1]}" >"$temporary"
mv "$temporary" "$output"
```

The seven choices repeat weekly; replace them with your own. Run the script once and inspect `~/src/pages/today.md`. Add `[Today's pick](today.html)` to the homepage. The generator owns `today.md`; edit the choices in the script, not its generated output.

Add this line to `[Service]` before `ExecStart`:

```ini
ExecStartPre=/bin/bash %h/scripts/todays-pick.sh
```

Each successful build now generates the pick first. If generation fails, systemd will not proceed to the build. Reload the units, run the service, inspect its journal, and check the published `/today.html` page. This is scheduled static content: the server builds a new page; visitors' browsers do not generate it. The generator and homepage link are the daily-pick challenge; refreshing a system report is not required.

To prove the timer publishes a change, first run the configured service and confirm `/today.html` shows today's pick. Edit that weekday's choice in `todays-pick.sh`; leave generated `today.md` alone. Stop the timer and wait for any build to finish. In `micro ~/.config/systemd/user/site-build.timer`, temporarily replace `OnCalendar` with `OnActiveSec=30s`, then save and quit. Reload the units, inspect the effective timer with `systemctl --user cat site-build.timer`, and start it. Wait for a new journal activation and verify the changed pick at `/today.html` without manually running the generator or build. Stop the timer; edit the complete unit to restore `OnCalendar=*-*-* 09:00:00`; reload, inspect the unit, then start it and check the next deadline.

Make the page feel like yours, and leave the normal daily 09:00 schedule active when done.

## If It Does Not Work

- Read `journalctl --user -u site-build.service --no-pager -n 50` for the first failing command.
- Confirm `systemctl --user list-timers --all site-build.timer` shows a next run.
- After changing a unit, run `systemctl --user daemon-reload`; stop and start the timer when changing its deadline.
- A build only publishes existing source unless its service explicitly runs your generator first.

For another self-contained timer example, see [the systemd timer card](../../commands/systemd-timer.md).
