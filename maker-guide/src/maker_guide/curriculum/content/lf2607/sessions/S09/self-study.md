# S9 Self-Study: Keep Your Website Up To Date

Session: S9

2026-10-10

## The idea

A systemd timer is the **when**; its matching service is the **what**. A oneshot service runs a finite task and exits. It is separate from the always-running web server. Timers are useful for daily site builds, rotating recommendations, scheduled reminders, and refreshing dashboards.

`OnCalendar=hourly` means at each clock hour. `RandomizedDelaySec=55min` spreads starts over a window of up to 55 minutes; it is neither strict concurrency spacing nor a real-time start guarantee. Check the calendar occurrence with `systemd-analyze calendar hourly`.

## Build each hour

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
Description=Build my website every hour

[Timer]
OnCalendar=hourly
RandomizedDelaySec=55min

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

The session resource starter at [/docs/sessions/S09/resources/singapore-today.sh](/docs/sessions/S09/resources/singapore-today.sh) fetches bounded Open-Meteo weather and air-quality responses and validates schema, units and dates. Copy it once and keep your own edits:

```bash
mkdir -p ~/scripts
cp /docs/sessions/S09/resources/singapore-today.sh \
    ~/scripts/singapore-today.sh
micro ~/scripts/singapore-today.sh
```

The daily maximum is a forecast in °C. CAMS PM2.5 is modelled μg/m³, not Singapore's official PSI or a local-station reading; do not provide health advice.

For an unrelated JSON-to-Markdown example, these standalone commands turn a book title into a short file. Keep this example separate from the weather artifacts:

```bash
title=$(echo '{"title":"Dune"}' | jq -r '.title')
printf '# Reading\n\nBook: %s\n' "$title" > /tmp/reading.md
cat /tmp/reading.md
```

Complete these steps in order, keeping these artifacts for inspection:

1. Fetch weather JSON to `~/playground/singapore/weather.json` and inspect its daily fields and units with `jq`.
2. Extract the daily maximum into `~/playground/singapore/temperature.txt`; it must be numeric and match the saved JSON snapshot.
3. Save and inspect `~/playground/singapore/air.json` and `~/playground/singapore/air.txt`. Use labelled lines `PM2.5: <value> μg/m³` and `Model time: <timestamp>`; both values must match the JSON.
4. Use a shell variable and `printf` to create `~/playground/singapore/forecast.md` with a heading and a line `Maximum: <value> °C`, matching the snapshot.
5. Finish the copied script to generate `~/src/pages/singapore-today.md`. Include labelled forecast date, maximum temperature, rain probability, sunrise, sunset, PM2.5, model timestamp, and retrieval time, with units and Open-Meteo/CAMS attribution. Keep API dates and times in ISO format; include the retrieval timezone or UTC offset in its timestamp. Keep validation, nonempty-field checks, and atomic replacement; remove the starter's incomplete-exercise stop only when finished.
6. Link `[Singapore today](singapore-today.html)` from `~/src/pages/index.md`; after a build inspect `~/public_html/singapore-today.html` for the complete bulletin. The browser displays static content, not live API data.
7. Add `ExecStartPre=/bin/bash %h/scripts/singapore-today.sh` before the build helper in the user service. Preserve its working directory, helper, hourly timer, and 55-minute randomized delay. The next-timer listing proves configuration only, not execution or publication.

Do not claim live freshness unless you actually run the generator and service and inspect the published page.

## If It Does Not Work

- Read `journalctl --user -u site-build.service --no-pager -n 50` for the first failing command.
- Confirm `systemctl --user list-timers --all site-build.timer` shows a next run.
- After changing a unit, run `systemctl --user daemon-reload`; stop and start the timer when changing its deadline.
- A build only publishes existing source unless its service explicitly runs your generator first.

For another self-contained timer example, see [the systemd timer card](../../commands/systemd-timer.md).
