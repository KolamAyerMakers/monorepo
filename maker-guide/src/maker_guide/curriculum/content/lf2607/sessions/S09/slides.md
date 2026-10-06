# Update Your Website Automatically

Session: S9

2026-10-10

Your web service keeps running, but your system report still needs fresh data.

How can you collect new system facts and rebuild your website on a schedule?

<!-- end_slide -->

# Automate Updates And Preserve Your Work

1. Schedule your report script and website build so new system facts appear on your website automatically.
2. Keep short personal notes on how to understand and operate your site.

Save your README, website source, scripts, and service and timer files in Git and Forgejo.

<!-- end_slide -->

# One Task, In Order

```text
report script -> report facts -> build -> published site
```

A failed report must stop the build and keep the last valid report. Never publish a partial report.

<!-- end_slide -->

# Three Different Jobs

- `site.service` keeps serving the published files.
- `site-build.service` runs one report refresh and build, then becomes inactive.
- `site-build.timer` starts that finite task on a schedule.

The timer does not replace the web service.

<!-- end_slide -->

# The Build Must Wait For The Report

`Type=oneshot` means systemd waits for the task to finish. `ExecStartPre` runs before `ExecStart`; a nonzero result prevents the build.

The timer and service share a name: `site-build.timer` activates `site-build.service`.

<!-- end_slide -->

# When The Timer Runs

- `OnActiveSec` counts from timer activation.
- `OnUnitInactiveSec` counts from the service finishing.
- `WantedBy=timers.target` lets you enable the timer.

The schedule is approximate, not an exact execution time. `AccuracySec=1s` narrows the scheduling window for observation; it is not real-time timing.

<!-- end_slide -->

# Prepare The Existing Project

In your classroom account, confirm the project, scripts, web service, and report are present. Inspect the report script before unattended use; preserve changes when upgrading an old direct-write copy.

Follow [project prerequisites](self-study.md#keep-the-same-project) and [the report safety gate](self-study.md#report-safety-gate). Do not schedule until the script preserves the last valid report on failure.

<!-- end_slide -->

# Pause Before Editing Units

Stop any existing timer. A running build does not stop with its timer; wait for it to finish, and do not run a terminal build alongside it.

```bash
systemctl --user stop site-build.timer
systemctl --user status site-build.service --no-pager
systemctl --user cat site-build.service site-build.timer
mkdir -p ~/.config/systemd/user
micro ~/.config/systemd/user/site-build.service
micro ~/.config/systemd/user/site-build.timer
```

On first setup, a missing unit is expected. Inspect existing units and drop-ins before replacing settings.

<!-- end_slide -->

# A Task Described Once

`~/.config/systemd/user/site-build.service`:

```ini
[Unit]
Description=Refresh report and build my site

[Service]
Type=oneshot
WorkingDirectory=%h/src
ExecStartPre=/bin/bash %h/scripts/maker-report.sh "System Report"
ExecStart=/usr/local/bin/npm run build
```

`ExecStartPre` runs first; a nonzero exit stops the build. `build-website` is an alias for your shell, not an executable for systemd.

A oneshot service runs its task and returns to inactive. That is normal.

<!-- end_slide -->

# The Timer Decides When

`~/.config/systemd/user/site-build.timer`:

```ini
[Unit]
Description=Observe automatic refresh and build

[Timer]
OnActiveSec=30s
OnUnitInactiveSec=2min
AccuracySec=1s

[Install]
WantedBy=timers.target
```

Same name, different suffix: this timer starts `site-build.service`. The short delays are for this classroom observation. We will change them to hourly.

<!-- end_slide -->

# Load And Run A Manual Baseline

Reload and inspect the effective units, then run one service baseline. A successful oneshot normally ends inactive. Do not enable the timer unless the journal confirms successful completion.

```bash
systemctl --user daemon-reload
systemctl --user cat site-build.service site-build.timer
systemctl --user start site-build.service
journalctl --user -u site-build.service --no-pager -n 50
```

<!-- end_slide -->

# Capture The Baseline

Keep the timer stopped. Record the source report and public response in a unique directory; stop if copying or fetching fails.

```bash
observation_directory="$(mktemp -d /tmp/site-automation.XXXXXX)"
date
cp ~/src/pages/maker-report.md "$observation_directory/before.md"
curl -fsS "https://lf2607.kolamayermakers.org/~$USER/maker-report.html" -o "$observation_directory/before.html"
```

<!-- end_slide -->

# Observe A New Automatic Activation

Only after the successful baseline, enable the timer and follow its journal. The timer listing is not evidence of execution.

```bash
systemctl --user enable --now site-build.timer
systemctl --user list-timers --all site-build.timer
journalctl --user -u site-build.service -f
```

Wait for a successful activation after the recorded time, roughly 30 seconds plus build time. Press Ctrl-C to leave the follower, then stop the timer and wait for the build to finish.

<!-- end_slide -->

# Prove Changed Facts Were Published

Fetch only after the build finishes. Compare old and new source facts, old and new public output, then public output with generated output:

```bash
systemctl --user stop site-build.timer
systemctl --user status site-build.service --no-pager
curl -fsS "https://lf2607.kolamayermakers.org/~$USER/maker-report.html" -o "$observation_directory/after.html"
diff -u "$observation_directory/before.md" ~/src/pages/maker-report.md
diff -u "$observation_directory/before.html" "$observation_directory/after.html"
diff -u ~/public_html/maker-report.html "$observation_directory/after.html"
journalctl --user -u site-build.service --no-pager -n 50
```

The first two diffs should show changed facts; the last should be identical. Diff exit 1 means differences; errors or exit above 1 invalidate the comparison. A failed fetch means stop, not compare.

<!-- end_slide -->

# Hourly From Now On

Stop the timer, wait for any build to finish, and replace the classroom timer with the hourly schedule. Inspect the effective unit for old additive schedules and drop-ins; see [timing caveats](self-study.md#hourly-schedule).

```ini
OnActiveSec=1h
OnUnitInactiveSec=1h
```

```bash
systemctl --user daemon-reload
systemctl --user cat site-build.timer
systemctl --user enable --now site-build.timer
systemctl --user list-timers --all site-build.timer
```

Do not accumulate schedules. Reloading does not reset activation; enable --now does not restart an already active timer. Stop before editing, then enable/start to re-arm it.

<!-- end_slide -->

# Leave Yourself Useful Notes

Add a heading and brief description, useful paths and links, and the commands you use to refresh, pause, resume, and inspect your service and logs. Keep useful existing notes.

<!-- end_slide -->

# Preserve Five Working Files

| Active files | Source copies |
|---|---|
| `~/scripts/maker-report.sh`, `~/scripts/site-check.sh` | `~/src/scripts/` |
| `site.service`, `site-build.service`, `site-build.timer` in `~/.config/systemd/user/` | `~/src/services/` |

Copy, do not move. Follow [Prepare a source handoff](../../quests/prepare-source-handoff.md) to commit, push, and verify the files in Forgejo. Pause the timer and wait for builds before copying or committing; resume the reviewed hourly timer afterward.

<!-- end_slide -->

# Exit Evidence

Show a timer run you did not start, with changed report facts and a matching journal entry.

Show your saved personal notes and the pushed scripts and units.

Explain what collects the facts, what builds the site, and what happens when collection fails.

<!-- end_slide -->

# Next: Show What You Can Do

S10 is 2026-10-24: a short celebration of the work, with your websites and reports on screen.

No preparation required. Bring your project and your questions.
