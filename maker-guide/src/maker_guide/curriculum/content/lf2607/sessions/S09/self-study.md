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

## Challenge: publish Singapore conditions

The session resource starter at [/docs/sessions/S09/resources/singapore-today.sh](/docs/sessions/S09/resources/singapore-today.sh) fetches bounded Open-Meteo weather and air-quality responses, validates schema, units and dates, then stops before extraction and publication. It intentionally exits `EXERCISE_INCOMPLETE`; removing that diagnostic alone cannot publish placeholders or an empty report. Copy it once and keep your own edits:

```bash
mkdir -p ~/scripts
cp /docs/sessions/S09/resources/singapore-today.sh ~/scripts/singapore-today.sh
micro ~/scripts/singapore-today.sh
```

The daily maximum is a forecast, not current temperature. The air value is CAMS model data, not Singapore's official PSI or a local-station reading; give no health advice. Inspect the temporary JSON and complete both TODO sections. Example extraction and redirection:

```bash
jq -r '.daily.temperature_2m_max[0]' "$temporary_directory/weather.json" > "$temporary_directory/example.txt"
```

Use command substitution to fill each required variable; compose Markdown with `printf` redirected into the temporary report. Keep the source forecast date and air-model timestamp distinct from retrieval time. Attribute Open-Meteo and CAMS; do not mislabel model PM2.5 as PSI.

| Report field | JSON field | Meaning / unit |
|---|---|---|
| Forecast date | `.daily.time[0]` | date in Asia/Singapore |
| Maximum temperature | `.daily.temperature_2m_max[0]` | forecast °C |
| Rain probability | `.daily.precipitation_probability_max[0]` | % |
| Sunrise and sunset | `.daily.sunrise[0]`, `.daily.sunset[0]` | local timestamps |
| Modelled PM2.5 | `.current.pm2_5` | μg/m³, CAMS estimate |
| Model timestamp | `.current.time` | API timestamp |
| Retrieved | generated with `date` | script retrieval time |

After completing both exercises, run with an output under `~/src/pages/` and inspect the report. Fetch or validation failures preserve an existing report. Add `[Singapore today](singapore-today.html)` to `~/src/pages/index.md`.

Add `ExecStartPre=/bin/bash %h/scripts/singapore-today.sh` before `ExecStart` in the service. Failure prevents the build and leaves the previous report. Inspect the journal and `/singapore-today.html`; this is scheduled static content, not browser-generated data. Prove the automatic path with the classroom timer, then restore and leave the normal daily schedule active. Personalize the script's Markdown heading and verify a new retrieval time after a timer activation; do not manually run the generator or build during the proof.

## If It Does Not Work

- Read `journalctl --user -u site-build.service --no-pager -n 50` for the first failing command.
- Confirm `systemctl --user list-timers --all site-build.timer` shows a next run.
- After changing a unit, run `systemctl --user daemon-reload`; stop and start the timer when changing its deadline.
- A build only publishes existing source unless its service explicitly runs your generator first.

For another self-contained timer example, see [the systemd timer card](../../commands/systemd-timer.md).
