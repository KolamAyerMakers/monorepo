# Schedule site rebuilds

Quest: schedule-site-rebuilds

## Mission

Automatically refresh the system report's facts, then build the existing site. Prove a timer-triggered run with logs and changed published content, not just a timer listing.

## Before You Start

Keep the existing `~/scripts/maker-report.sh`, `~/scripts/site-check.sh`, and `site.service`. The report script takes one title and writes `~/src/pages/maker-report.md`. npm builds that Markdown; it does not collect new report facts.

Follow [report preparation](../sessions/S09/self-study.md#report-safety-gate) to compare and safely upgrade an older script. The current resource stops on errors and preserves the last valid report until a replacement is complete. A nonzero report exit must prevent the build.

## Files To Create

Use the [S9 setup sequence](../sessions/S09/self-study.md#timer-files) to pause any existing timer, wait for builds to finish, and inspect existing units before editing. Active units belong in `~/.config/systemd/user/`.

`site-build.service`:

```ini
[Unit]
Description=Refresh report and build my site

[Service]
Type=oneshot
WorkingDirectory=%h/src
ExecStartPre=/bin/bash %h/scripts/maker-report.sh "System Report"
ExecStart=/usr/local/bin/npm run build
```

`%h` means your home directory. A failed pre-start command stops the chain. Do not prefix it with `-`, which would ignore failure. `build-website` is an interactive alias and cannot be used as the systemd executable.

`site-build.timer`, for a short classroom observation:

```ini
[Unit]
Description=Observe automatic report refresh and build

[Timer]
OnActiveSec=30s
OnUnitInactiveSec=2min
AccuracySec=1s

[Install]
WantedBy=timers.target
```

The first deadline is relative to timer activation; repeats wait until two minutes after the service finishes. The matching timer activates the oneshot, not the long-running web server. Systemd does not start another copy of an active service, but cannot prevent a competing terminal build. Do not run npm or the build alias alongside it.

## Observe, Then Slow Down

1. Follow [Establish A Baseline](../sessions/S09/self-study.md#establish-a-baseline): reload, inspect the effective units, manually run once, and resolve errors with the timer stopped.
2. Save the baseline report Markdown and public HTML in a fresh scratch directory.
3. Follow [Witness Automatic Publication](../sessions/S09/self-study.md#witness-automatic-publication): start the timer, record the time, and watch for a new journal activation without manually building.
4. After completion, stop the timer and wait for any active build. Fetch again and compare the old and new facts, including the report date, then compare the public body with generated HTML. Refresh the laptop browser too.
5. Replace the short timer with the complete [hourly schedule](../sessions/S09/self-study.md#hourly-schedule): `OnActiveSec=1h` and `OnUnitInactiveSec=1h`. Remove old timing directives rather than accumulating schedules. Inspect drop-ins, reload while stopped, then start and inspect the actual next deadline.
6. Preserve the working units using [Prepare a source handoff](prepare-source-handoff.md).

## Evidence And Recovery

A successful oneshot normally becomes inactive after finishing. Read the journal for a completed run after timer activation and show the corresponding changed public report. A failed request, unchanged report, or manual run is not that evidence.

If refresh fails, the build must not start and the previous valid report must remain. If the unit or schedule is wrong, stop the timer, let a running build finish, inspect `systemctl --user cat site-build.service site-build.timer`, and repair the first error from `journalctl --user -u site-build.service --no-pager -n 50`.

Reloading alone does not reset an active timer's clock. Stop, edit, reload, then start when changing its schedule. These monotonic timers do not replay missed hourly runs after downtime. If automation stops at logout, inspect `loginctl show-user "$USER" -p Linger` and ask staff; do not change shared system settings yourself.

## Related Reading

- [systemd timer](../commands/systemd-timer.md)
- [systemctl list-timers](../commands/systemctl-list-timers.md)
- [automation timers](../concepts/automation-timers.md)
- [systemd timer units](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)
