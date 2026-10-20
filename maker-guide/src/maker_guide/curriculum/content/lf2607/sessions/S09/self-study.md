# S9 — Keep Your Website Up to Date

Fetch a forecast, turn JSON into a page, and schedule generation before publication.

**You need:** curl, jq, Bash, your site source, and a working systemd user manager. These exercises need Internet access. At home, use [Continue at Home](../../guides/continue-at-home.md); a public website is not required.

## Before fetching

An API returns structured data. **JSON** objects have named fields; arrays hold ordered values. In jq, `.daily.temperature_2m_max[0]` means: the `daily` object → its temperature array → the first value. `-r` prints a string without JSON quotes.

We use Singapore coordinates `1.32411, 103.8698`. Forecast temperatures are °C. PM2.5 is modelled by CAMS Global in μg/m³—not a station reading or official Singapore PSI. Forecast/model timestamps use Singapore time; retrieval time describes when you fetched them.

Keep a working script or page if repeating the lesson. The early exercises overwrite only their named practice files.

## Build the bulletin

### 1. Fetch and inspect weather

**Goal:** save one day's forecast and understand its shape.

**Do:**

```bash
mkdir -p ~/playground/singapore
curl -fsS --max-time 15 'https://api.open-meteo.com/v1/forecast?latitude=1.32411&longitude=103.8698&daily=temperature_2m_max,precipitation_probability_max,sunrise,sunset&timezone=Asia%2FSingapore&forecast_days=1' -o ~/playground/singapore/weather.json
jq '{daily: .daily, units: .daily_units}' ~/playground/singapore/weather.json
```

**Check:** identify the date, maximum, rain probability, sunrise, sunset, and units. Each daily array has one day's value.

**Fix:** read curl's error and retry. Do not continue with partial JSON. `-f` makes HTTP errors fail, unlike our S6 diagnostic checker; `-sS` keeps errors visible.

### 2. Extract maximum temperature

**Goal:** select a value, not copy it by hand.

**Do:**

```bash
jq -r '.daily.temperature_2m_max[0]' ~/playground/singapore/weather.json > ~/playground/singapore/temperature.txt
cat ~/playground/singapore/temperature.txt
jq -r '.daily.temperature_2m_max[0]' ~/playground/singapore/weather.json
```

**Check:** both numbers match the first temperature in the JSON.

**Fix:** check the selector. `null` is not a temperature; inspect the response instead of publishing it.

### 3. Save air quality

**Goal:** preserve the model value and its timestamp.

**Do:**

```bash
curl -fsS --max-time 15 'https://air-quality-api.open-meteo.com/v1/air-quality?latitude=1.32411&longitude=103.8698&current=pm2_5&timezone=Asia%2FSingapore&domains=cams_global' -o ~/playground/singapore/air.json
jq '{current: .current, units: .current_units}' ~/playground/singapore/air.json
printf 'PM2.5: %s μg/m³\nModel time: %s\n' "$(jq -r '.current.pm2_5' ~/playground/singapore/air.json)" "$(jq -r '.current.time' ~/playground/singapore/air.json)" > ~/playground/singapore/air.txt
cat ~/playground/singapore/air.txt
```

**Check:** the labelled number and time match `.current.pm2_5` and `.current.time`.

**Fix:** inspect those fields and units. Do not replace missing values with invented numbers.

### 4. Format a small page

**Goal:** use the same saved snapshot to generate Markdown.

**Do:**

```bash
temperature=$(jq -r '.daily.temperature_2m_max[0]' ~/playground/singapore/weather.json)
printf '# Singapore forecast\n\nMaximum: %s °C\n' "$temperature" > ~/playground/singapore/forecast.md
cat ~/playground/singapore/forecast.md
```

**Check:** one heading and the matching maximum. Quotes keep the variable as one argument.

**Fix:** check assignment syntax—no spaces around `=`—and the jq result.

### 5. Complete the generator

**Goal:** fetch fresh data and write a complete bulletin.

**Do:** in class, copy the starter; `-i` protects an existing script:

```bash
mkdir -p ~/scripts
cp -i /docs/sessions/S09/resources/today.sh ~/scripts/today.sh
micro ~/scripts/today.sh
```

At home, copy from `~/linux-foundations-practice/starters/today.sh` instead.

The starter downloads the two JSON responses and assigns `retrieved=$(date)`. Finish its two TODOs:

1. Assign these variables with `jq -r` and `$()`:

| Variable | Selector | File |
|---|---|---|
| `forecast_date` | `.daily.time[0]` | `weather.json` |
| `temperature` | `.daily.temperature_2m_max[0]` | `weather.json` |
| `rain` | `.daily.precipitation_probability_max[0]` | `weather.json` |
| `sunrise` | `.daily.sunrise[0]` | `weather.json` |
| `sunset` | `.daily.sunset[0]` | `weather.json` |
| `air_time` | `.current.time` | `air.json` |
| `pm25` | `.current.pm2_5` | `air.json` |

2. Use grouped `printf` commands and `>` to write `~/src/pages/today.md`, as in S5. Include:
   - Forecast date, maximum (°C), rain probability (%), sunrise, and sunset.
   - PM2.5 (μg/m³), model time, and retrieval time.
   - Singapore timezone, coordinates, and sources: Open-Meteo forecast; CAMS Global via Open-Meteo.
   - The distinction between modelled PM2.5, a station reading, and official PSI.

Keep API timestamps unchanged. In a `printf` **format**, use `%%` for a literal `%`; quote each variable argument. Remove the `EXERCISE_INCOMPLETE` comment when finished.

```bash
bash -n ~/scripts/today.sh
bash ~/scripts/today.sh
cat ~/src/pages/today.md
```

**Check:** every field matches the saved JSON, with labels, units, timestamps, and attribution.

**Fix:** compare with [the worked generator](../../guides/self-study-answers.md#s9-bulletin-and-timer). Before scheduling, use its checked, failure-preserving version or add equivalent handling: failed downloads or missing fields must not replace your last good bulletin.

### 6. Link and publish

**Goal:** reach the bulletin from the homepage.

**Do:** add `[Singapore today](today.html)` to `~/src/pages/index.md`. Build with `build-website` in class, or `cd ~/src && node scripts/build.mjs` at home. Then:

```bash
grep -n 'today.html' ~/public_html/index.html
grep -n 'Singapore\|PM2.5\|Open-Meteo\|CAMS' ~/public_html/today.html
```

**Check:** open the homepage, follow its link, and inspect the bulletin. It is a saved snapshot, not a live API request from the browser.

**Fix:** correct source or generation, then rebuild. Inspect the rendered page, not only grep's matches.

### 7. Schedule generation before building

**Goal:** define the task and its schedule separately.

A **oneshot service** performs a task and exits. A **timer** decides when to start it. Neither replaces your always-running web server.

**Do:** create `~/.config/systemd/user/site-build.service`:

```ini
[Unit]
Description=Generate and publish my bulletin

[Service]
Type=oneshot
WorkingDirectory=%h/src
ExecStartPre=/bin/bash %h/scripts/today.sh
ExecStart=/usr/local/bin/maker-guide-build-personal-website
```

**At home**, replace the last line with `ExecStart=/usr/bin/node %h/src/scripts/build.mjs`, substituting the actual absolute Node path from `command -v node`. If Node is in a version-manager directory, also set `Environment=PATH=ACTUAL_NODE_DIRECTORY:/usr/local/bin:/usr/bin:/bin` in `[Service]`. Use the real directory, not that placeholder or `$PATH`: systemd does not load your interactive shell setup.

Create `~/.config/systemd/user/site-build.timer`:

```ini
[Unit]
Description=Publish my bulletin hourly

[Timer]
OnCalendar=hourly
RandomizedDelaySec=55min

[Install]
WantedBy=timers.target
```

`hourly` means each clock hour, plus a random delay of up to 55 minutes. It spreads starts; it is not precise concurrency spacing. The matching filename makes this timer start `site-build.service`.

```bash
systemd-analyze --user verify ~/.config/systemd/user/site-build.service ~/.config/systemd/user/site-build.timer
```

Resolve verification errors, then load and run manually:

```bash
systemctl --user daemon-reload
systemctl --user start site-build.service
journalctl --user -u site-build.service --no-pager -n 30
```

Confirm the manual run published the correct page before enabling the schedule:

```bash
systemctl --user enable --now site-build.timer
systemctl --user list-timers --all site-build.timer
```

`ExecStartPre` must succeed before the build runs. The class helper is the executable behind `build-website`; systemd cannot use an interactive alias.

**Check:** the manual run generates and publishes the page; the timer is enabled, active, and lists a next run. Later, compare a scheduled journal entry and retrieval time with the published page. A deadline alone does not prove execution.

**Fix:** read the first service error. After changing a timer, run `daemon-reload` and restart the timer. A completed oneshot is normally inactive; that alone is not failure.

## Stop the schedule

When you no longer want hourly requests:

```bash
systemctl --user disable --now site-build.timer
```

This removes future scheduling; it does not cancel a build already running. User timers need a running user manager. Sleeping/stopped environments cannot execute the task; this timer does not catch up every missed hour.

## Check yourself

- Explain how a jq selector reaches an array's first value.
- Explain why generation must happen before publication.
- Explain why an active timer and an inactive oneshot can both be normal.
- What should remain published after an API failure?

[Answers](../../guides/self-study-answers.md#s9-bulletin-and-timer). Reference: [systemd timer](../../commands/systemd-timer.md). Use the providers' current terms and limits before adapting the API to a larger project.
