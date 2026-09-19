# S9 Self-Study: Automate It. Hand It Over.

Session: S9

2026-10-10

## Two Workshops

1. Automatically refresh report facts, then build. Prove a real timer activation with logs and changed published content.
2. Peer-test an operations README and push a recoverable source handoff.

Allow 15 minutes for preparation, 60 for automation, a 10-minute break, 75 for the handoff workshop, and 20 for verification. S10 is on **2026-10-24**.

## Keep The Same Project

Run these commands in your own classroom SSH account, not on your laptop or a puzzle server:

```bash
whoami
hostname
pwd
ls -l ~/scripts/maker-report.sh ~/scripts/site-check.sh
git -C ~/src status
systemctl --user cat site.service
bash ~/scripts/site-check.sh "" maker-report.html
```

Keep the existing site, report generator, checker, and web service. The checker takes page arguments: `""` means the homepage. Read both results; an HTTP request completing is not proof that the page succeeded. If `~/src` is not a repository, recover through the [S4 Git workflow](../S04/self-study.md#git-workflow), not a second project.

Before automated publishing, inspect `site.service`. It must use `WorkingDirectory=%h` and `ExecStart=/usr/bin/caddy file-server --listen :12345 --root %h/public_html --access-log`, replacing `12345` with your numeric `10000 + uid` port. If the result exceeds `65535`, ask the instructor; do not choose another port. The publisher swaps the output directory; explicit `--root` follows the new path instead of an old working directory. Use the complete [S8 unit and preservation steps](../S08/self-study.md#2-create-the-user-unit) if your unit needs updating, then reload and restart the web service.

Personal Caddy listens for HTTP on all interfaces; the classroom firewall blocks new direct external connections to its port. Shared Caddy handles public HTTPS and forwards requests over loopback. Same software, two separate processes. Do not add `--domain` or change shared configuration. `file-server` disables its admin API. Use `systemctl --user` to control your service, never `caddy stop` or `caddy reload`, which can target shared Caddy's admin endpoint. The explicit root is not a sandbox; keep secrets and symlinks to private files out of the published tree.

## Report Safety Gate

Read your installed script before scheduling it:

```bash
cat ~/scripts/maker-report.sh
cat ~/src/pages/maker-report.md
```

The [provided report generator](../S06/self-study.md#provided-report-script) accepts one title and writes `~/src/pages/maker-report.md`. It collects into a temporary file, stops on errors, and replaces the report only after a complete successful write. A collection or publication failure preserves the last valid report.

An older copy from S5 may write straight into the destination. Preserve your changes before replacing it with the current classroom resource:

```bash
backup_directory="$(mktemp -d "$HOME/report-script-backup.XXXXXX")"
cp ~/scripts/maker-report.sh "$backup_directory/maker-report.sh"
diff -u ~/scripts/maker-report.sh /docs/guides/resources/maker-report.sh
```

Stop if the backup fails. A diff exit of `1` means the scripts differ. Read the differences; preserve any personal additions with the instructor's help. Once you agree to the replacement:

```bash
cp -i /docs/guides/resources/maker-report.sh ~/scripts/maker-report.sh
```

Confirm the installed copy has temporary-file publication and error handling before scheduling it. Do not deliberately break the live report to test an old script. A failed `ExecStartPre` prevents the build; a successful npm build alone cannot prove collection succeeded.

## Timer Files

Pause an existing timer before changing its files:

```bash
systemctl --user stop site-build.timer
systemctl --user status site-build.service --no-pager
```

On the first setup, `Unit ... not found` is expected. Otherwise, if the build service is still `activating`, let it finish and repeat the status command. Do not stop it mid-publication. Resolve a failure from its journal before continuing. Also let any manually started build finish; do not run the alias or npm alongside this workshop.

Inspect existing files before editing; preserve unrelated settings deliberately. Create these two complete units with Micro, saving with `Ctrl-S` and quitting with `Ctrl-Q`:

```bash
mkdir -p ~/.config/systemd/user
micro ~/.config/systemd/user/site-build.service
micro ~/.config/systemd/user/site-build.timer
```

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

`%h` is your home directory. Bash receives `System Report` as one title argument. Systemd does not run `ExecStart` in your interactive shell: `build-website` is an alias, not an executable. `/usr/local/bin/npm run build` in the existing `~/src` project runs its build pipeline, but does not regenerate report facts by itself.

`~/.config/systemd/user/site-build.timer`, for classroom observation:

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

The matching name selects `site-build.service`. `OnActiveSec` counts from timer activation, not machine boot. `OnUnitInactiveSec` waits two minutes after the service finishes, rather than launching work repeatedly during a slow build. `AccuracySec` narrows the normal scheduling window for the classroom demonstration; it is not a hard real-time guarantee.

Systemd will not start a second copy of the same active service. That does not serialize unrelated terminal builds. Use the service for refresh-and-build work; pause the timer and wait for the service to finish before any standalone report generation or build. Do not add `RemainAfterExit=yes`, which would leave the oneshot active and prevent repeated runs.

## Establish A Baseline

Keep the timer stopped. Load the units, inspect the effective configuration, and run the service once manually to discover setup errors before scheduling it:

```bash
systemctl --user daemon-reload
systemctl --user cat site-build.service site-build.timer
systemctl --user start site-build.service
journalctl --user -u site-build.service --no-pager -n 50
```

Stop here if the start fails. Read the first real error; do not enable automatic retries of broken work. A successful oneshot normally ends as `inactive (dead)`. Its journal should show completion, not a pre-start or build failure. Check that no old drop-in adds another schedule or ignores report failure with a `-` prefix.

Capture a baseline without overwriting existing files:

```bash
observation_directory="$(mktemp -d /tmp/site-automation.XXXXXX)"
cp ~/src/pages/maker-report.md "$observation_directory/before.md"
curl -fsS "https://lf2607.kolamayermakers.org/~$USER/maker-report.html" -o "$observation_directory/before.html"
```

Stop if creating, copying, or fetching fails. Keep this terminal open: the variable names your evidence directory. Open the report in your laptop browser too, using your actual classroom username rather than typing `$USER` literally.

## Witness Automatic Publication

Start the timer and follow the journal. Do not manually start the service or run a build while waiting:

```bash
date
systemctl --user enable --now site-build.timer
systemctl --user list-timers --all site-build.timer
journalctl --user -u site-build.service -f
```

Wait for a new activation after the recorded time, roughly 30 seconds plus build time. The old manual run is not the evidence. After the new successful completion, press `Ctrl-C` to leave the journal follower, not to stop the service. Pause the timer so comparisons stay stable:

```bash
systemctl --user stop site-build.timer
systemctl --user status site-build.service --no-pager
```

If another build is running, wait for completion before fetching. Nobody should run another build in a second terminal. Then:

```bash
curl -fsS "https://lf2607.kolamayermakers.org/~$USER/maker-report.html" -o "$observation_directory/after.html"
diff -u "$observation_directory/before.md" ~/src/pages/maker-report.md
diff -u "$observation_directory/before.html" "$observation_directory/after.html"
diff -u ~/public_html/maker-report.html "$observation_directory/after.html"
journalctl --user -u site-build.service --no-pager -n 50
bash ~/scripts/site-check.sh "" maker-report.html
```

Stop and diagnose failed fetches before comparing files. A `diff` exit of `1` means differences, not a command malfunction. The first two comparisons should show changed collected facts, including the report date. The last should show no differences: the public body matches generated output. An exit above `1` is a comparison error. Refresh the laptop browser and identify the same new date.

Record the activation time, new report date, and actual HTTP/body results. Merely listing a timer or rebuilding unchanged Markdown does not prove the workshop's automatic refresh.

## Hourly Schedule

Stop the timer and wait for any active build to finish as above. Replace the complete classroom timer with this file, not an additional block:

```ini
[Unit]
Description=Refresh report and build my site hourly

[Timer]
OnActiveSec=1h
OnUnitInactiveSec=1h

[Install]
WantedBy=timers.target
```

Remove the classroom `30s`, `2min`, and `AccuracySec=1s` settings. Also remove obsolete `OnBootSec`, `OnUnitActiveSec`, or `OnCalendar` schedules from this unit if present: timer expressions are additive, not alternatives. Inspect `systemctl --user cat site-build.timer` for drop-ins. If your own drop-in supplies an old schedule, edit that file too; an empty assignment to its timing directive clears earlier entries before a replacement. Do not alter settings you do not understand without the instructor's help.

```bash
systemctl --user daemon-reload
systemctl --user cat site-build.timer
systemctl --user enable --now site-build.timer
systemctl --user list-timers --all site-build.timer
```

Stopping before editing and starting after reload re-arms the timer's activation clock. `daemon-reload` alone does not do that, and `enable --now` does not restart an already active timer. The completion-relative deadline can still use the service's previous finish time; if that was over an hour ago, an immediate run can be due. Read the actual next deadline rather than promising exactly one hour from this command.

This monotonic schedule runs after timer activation and service completion, not on wall-clock hour boundaries. It does not replay missed hourly runs after downtime. For logout operation, inspect `loginctl show-user "$USER" -p Linger`; ask the instructor if lingering is needed. Do not change shared system policy yourself.

## Workshop 2: Peer-Test The README

Follow [Write your README](../../quests/write-readme.md). Explain purpose, public links, source/output paths, dependencies, refresh/build commands, timer control, logs, restoration, and one real recovery. State the difference between fresh facts and freshly rendered HTML.

The peer reads the README and directs the work; the owner reviews and types in their own account. Use the instructions to pause automation, refresh/build once, and inspect the result. Agree to a brief stop of the owner's `site.service`, observe the local failure, restart it, and verify local and public responses. Do not stop anyone else's processes or exchange passwords. Fix unclear instructions and swap roles.

Then follow [Prepare a source handoff](../../quests/prepare-source-handoff.md) for the five copy paths, runnable restoration, and scoped Git workflow. Keep automation paused and builds finished while copying and reviewing source, because report generation modifies a tracked Markdown page. Preserve the two scripts and three units, not only a list of commits. Verify the pushed files in Forgejo and restart the hourly timer when finished.

## Troubleshooting

| Observation | Next Step |
|---|---|
| Pre-start failure | Read the report error in the journal. The build must not run; preserve the previous report and fix collection. |
| npm failure | Inspect the build log and the existing project's dependencies. Do not bypass pre-start to claim success. |
| No automatic activation | Inspect the timer's state, effective schedule, next deadline, and user journal. A manual start is diagnosis, not automatic evidence. |
| Old report facts | Confirm `ExecStartPre`, the installed script, and the output path. A build alone is insufficient. |
| Static site fresh, service stale | Inspect the serving unit's working directory and explicit `--root`; reload and restart after correcting it. |
| Public service fails, local request works | Collect the outputs and ask the instructor about routing; do not change DNS, shared Caddy settings, or TLS verification. |
| Changes appear during Git review | Stop the timer, wait for the service and any manual build, then inspect again. |

## Optional Pointers

These are optional interests, not another workshop checklist or prerequisites:

- [Heading substitution with sed](../../quests/transform-heading-with-sed.md) and [awk](../../commands/awk.md).
- [Vim](../../commands/vim.md), if you want to try another editor.
- [Try cron and remove it](../../quests/try-cron-and-remove-it.md), preserving unrelated jobs and never scheduling a competing site build.
- [Enable the webring](../../quests/enable-webring.md), if that navigation is useful to your site.
- [systemd timer units](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html) and [service units](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html).
