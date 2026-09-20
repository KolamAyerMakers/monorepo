# Automate It. Hand It Over.

Session: S9

2026-10-10

Your service runs when asked. Can it run on its own?

<!-- end_slide -->

# Two Workshops

1. A timer refreshes the report and rebuilds the published site.
2. A peer operates your README, and you preserve the source handoff.

Keep the same site, scripts, and `site.service`. No new helper is needed.

<!-- end_slide -->

# One Task, In Order

```text
report script -> report facts -> build -> published site
```

A failed report must stop the build and keep the last valid report. Never publish a partial report.

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

[Install]
WantedBy=timers.target
```

Same name, different suffix: this timer starts `site-build.service`. The short delays are for this classroom observation. We will change them to hourly.

<!-- end_slide -->

# Prove It Ran Automatically

Save the current report, then start the timer:

```bash
cp ~/src/pages/maker-report.md "$HOME/report-before.md"
systemctl --user daemon-reload
systemctl --user enable --now site-build.timer
systemctl --user list-timers --all site-build.timer
journalctl --user -u site-build.service -f
```

Wait for a run you did not start, then compare the old and new report date. A timer listing is not proof; a new activation is.

<!-- end_slide -->

# Hourly From Now On

Stop the timer and let any build finish, then replace the two timing values:

```ini
OnActiveSec=1h
OnUnitInactiveSec=1h
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now site-build.timer
systemctl --user list-timers --all site-build.timer
```

Do not leave both the classroom and hourly schedules in place.

<!-- end_slide -->

# Workshop 2: Can A Peer Operate It?

Write an operations README: what runs, where it lives, how to refresh, how to inspect, how to recover.

The peer reads and directs. You run the commands in your own account.

No password sharing. When an instruction is unclear, improve it, then retry.

<!-- end_slide -->

# Test The Instructions

- Find the public page and its source.
- Refresh and build through the oneshot service.
- Agree to a brief stop, then recover the service from the README.
- Check local and public responses after recovery.

Swap roles. Record one ambiguity you fixed and one recovery you observed.

<!-- end_slide -->

# Preserve Five Working Files

| Active files | Source copies |
|---|---|
| `~/scripts/maker-report.sh`, `~/scripts/site-check.sh` | `~/src/scripts/` |
| `site.service`, `site-build.service`, `site-build.timer` in `~/.config/systemd/user/` | `~/src/services/` |

Copy, do not move. Follow [Prepare a source handoff](../../quests/prepare-source-handoff.md) to commit, push, and verify the files in Forgejo.

<!-- end_slide -->

# Exit Evidence

Show a timer run you did not start, with changed report facts and a matching journal entry.

Show the peer-tested README and the pushed scripts and units.

Explain what collects the facts, what builds the site, and what happens when collection fails.

<!-- end_slide -->

# Next: Show What You Can Do

S10 is 2026-10-24: a short celebration of the work, with your websites and reports on screen.

No preparation required. Bring your project and your questions.
