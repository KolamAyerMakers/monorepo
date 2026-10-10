# S9 Self-Study: Keep Your Website Up To Date

Session: S9

2026-10-10

## The idea

A systemd timer is the **when**; its matching service is the **what**. A oneshot service runs a finite task and exits. It is separate from the always-running web server. Timers are useful for daily site builds, rotating recommendations, scheduled reminders, and refreshing dashboards.

`OnCalendar=hourly` means at each clock hour. `RandomizedDelaySec=55min` spreads starts over a window of up to 55 minutes; it is neither strict concurrency spacing nor a real-time start guarantee. Check the calendar occurrence with `systemd-analyze calendar hourly`.

The installed `maker-guide-build-personal-website` helper is the executable behind the classroom's `build-website` shortcut. systemd does not run interactive shell aliases. The build renders existing source; it does not create new content by itself. User timers need the user manager running. See [lingering](../../concepts/lingering.md) for logout behavior.

## Exercise: publish Singapore conditions

Complete all seven steps in order, in the same SSH shell so `~/` refers to the same account. You need `curl` and `jq`; if either is missing, ask your mentor rather than installing packages. Forecast maxima are °C. CAMS PM2.5 is modelled μg/m³, not official Singapore PSI or a station reading.

### 1. Fetch and inspect weather
**Goal:** save today's forecast and inspect its shape.

**Do:**
```bash
mkdir -p ~/playground/singapore
curl -fsS --max-time 15 'https://api.open-meteo.com/v1/forecast?latitude=1.32411&longitude=103.8698&daily=temperature_2m_max,precipitation_probability_max,sunrise,sunset&timezone=Asia%2FSingapore&forecast_days=1' -o ~/playground/singapore/weather.json
jq '{daily: .daily, units: .daily_units}' ~/playground/singapore/weather.json
```
**Check:** daily time, maximum, rain probability, sunrise and sunset appear; units include °C and %. Then run `guide check`.
**Fix:** inspect curl's error and retry; do not proceed with empty/partial JSON.

### 2. Extract maximum temperature
**Goal:** save the first-day value and compare it to the source.
**Do:** run the commands below.
```bash
jq -r '.daily.temperature_2m_max[0]' ~/playground/singapore/weather.json > ~/playground/singapore/temperature.txt
cat ~/playground/singapore/temperature.txt
jq -r '.daily.temperature_2m_max[0]' ~/playground/singapore/weather.json
```
**Check:** both numeric values match; run `guide check`. **Fix:** use selector `.daily.temperature_2m_max[0]` and repeat.

### 3. Save and compare air quality
**Goal:** preserve the CAMS response and create labelled values.
**Do:** run the commands below.
```bash
curl -fsS --max-time 15 'https://air-quality-api.open-meteo.com/v1/air-quality?latitude=1.32411&longitude=103.8698&current=pm2_5&timezone=Asia%2FSingapore&domains=cams_global' -o ~/playground/singapore/air.json
jq '{current: .current, units: .current_units}' ~/playground/singapore/air.json
printf 'PM2.5: %s μg/m³\nModel time: %s\n' "$(jq -r '.current.pm2_5' ~/playground/singapore/air.json)" "$(jq -r '.current.time' ~/playground/singapore/air.json)" > ~/playground/singapore/air.txt
cat ~/playground/singapore/air.txt
```
**Check:** labelled value and `YYYY-MM-DDTHH:MM` match `.current.pm2_5` and `.current.time`; run `guide check`. **Fix:** verify those selectors and recreate the file.

### 4. Format a Markdown forecast
**Goal:** use a variable and `printf` with the same snapshot.
**Do:** run the commands below.
```bash
temperature=$(jq -r '.daily.temperature_2m_max[0]' ~/playground/singapore/weather.json)
printf '# Singapore forecast\n\nMaximum: %s °C\n' "$temperature" > ~/playground/singapore/forecast.md
cat ~/playground/singapore/forecast.md
```
**Check:** heading and matching `Maximum: <number> °C`; run `guide check`. **Fix:** check the assignment and `"$temperature"`, then rerun.

### 5. Complete the bulletin generator
**Goal:** finish a small starter script that generates a complete bulletin.

**Do:**
```bash
mkdir -p ~/scripts
cp /docs/sessions/S09/resources/today.sh ~/scripts/today.sh
vim ~/scripts/today.sh
```
The script downloads weather and air data to the fixed JSON paths from steps 1 and 3. TODO 1: assign `forecast_date`, `temperature`, `rain`, `sunrise`, `sunset`, `air_time`, and `pm25` with `jq -r` and command substitution, using selectors `.daily.time[0]`, `.daily.temperature_2m_max[0]`, `.daily.precipitation_probability_max[0]`, `.daily.sunrise[0]`, `.daily.sunset[0]`, `.current.time`, and `.current.pm2_5`. TODO 2: use `printf` redirection (`>`) to compose attributed Markdown at `~/src/pages/today.md`.

Include labelled forecast date, maximum (°C), rain probability (%), sunrise, sunset, PM2.5 (μg/m³), model time, and retrieval time. Keep the API date/time values as provided. Use the output of `date` for retrieval time; no particular format is required. Forecast and model times use Singapore time. Attribute forecast to Open-Meteo and air data to CAMS Global/Open-Meteo. Explicitly say PM2.5 is modelled, not official PSI or a station reading.

Example of the expected `~/src/pages/today.md` (illustrative values):

```markdown
# Singapore today

Location: 1.32411, 103.8698 — Asia/Singapore

## Forecast

* Date: 2026-10-10
* Temperature: 31.0 °C
* Rain probability: 100%
* Sunrise: 2026-10-10T06:48
* Sunset: 2026-10-10T18:54

## Air quality

* Time: 2026-10-10T12:00
* PM2.5: 89.2 μg/m³

PM2.5 is modelled, not a station measurement or official Singapore PSI.
Forecast and model times are in Singapore time.

Retrieved: Sat Oct 10 12:05:00 +08 2026

Sources: Open-Meteo weather forecast; CAMS Global air-quality model via Open-Meteo.
```

Generate the values from your JSON and `retrieved` variable, not these example numbers.
With `printf`, write `%%` to output a literal `%`, and quote variable arguments.

**Check:** finish both TODOs, remove the `EXERCISE_INCOMPLETE` comment, save, then:
```bash
bash -n ~/scripts/today.sh
bash ~/scripts/today.sh
cat ~/src/pages/today.md
guide check
```
Confirm every field, units, attribution, unchanged API times, and retrieval time.
**Fix:** correct syntax errors and check the JSON selectors if values are missing.

### 6. Link and inspect both pages
**Goal:** link the bulletin from the homepage and verify both rendered pages.

**Do:** add `[Singapore today](today.html)` to `~/src/pages/index.md` using `vim`, then:
```bash
/usr/local/bin/maker-guide-build-personal-website
grep -n 'today.html' ~/public_html/index.html
grep -n 'Singapore\|PM2.5\|Open-Meteo\|CAMS' ~/public_html/today.html
guide check
```
**Check:** homepage links to `today.html`; separate bulletin page contains the content. It is static, not live API data. Browse only to a personal URL actually supplied by the classroom; do not guess a hostname.
**Fix:** correct the source link and rebuild, or regenerate `today.md` and rebuild if bulletin output is incomplete.

### 7. Run the generator hourly
**Goal:** generate before each build and verify configuration plus one manual run.

**Do:** create both user unit files in the editor:
```bash
mkdir -p ~/.config/systemd/user
vim ~/.config/systemd/user/site-build.service
```
Put this complete service in the editor, save, then open the timer path and enter its complete contents:
```ini
[Unit]
Description=Build my website

[Service]
Type=oneshot
WorkingDirectory=%h/src
ExecStartPre=/bin/bash %h/scripts/today.sh
ExecStart=/usr/local/bin/maker-guide-build-personal-website
```
```bash
vim ~/.config/systemd/user/site-build.timer
```
```ini
[Unit]
Description=Build my website every hour

[Timer]
OnCalendar=hourly
RandomizedDelaySec=55min

[Install]
WantedBy=timers.target
```
systemd runs the installed helper, not an interactive alias. Load and test the service, inspect its journal and output, then enable the schedule:
```bash
systemctl --user daemon-reload
systemctl --user start site-build.service
journalctl --user -u site-build.service --no-pager -n 30
grep -n 'PM2.5\|Open-Meteo\|CAMS' ~/public_html/today.html
systemctl --user enable --now site-build.timer
systemctl --user list-timers --all site-build.timer
systemctl --user is-enabled site-build.timer
systemctl --user is-active site-build.timer
guide check
```
**Check:** manual run succeeds, journal has no error, page contains bulletin; timer is enabled and active. A completed oneshot is normally inactive; active timer may wait for deadline. Listing a deadline proves configuration, not future execution/publication.
**Fix:** after changing an active timer, restart it after daemon-reload. Read journal and correct failure. Do not wait for the randomized run as proof; manually start and inspect.

## If It Does Not Work

- Read `journalctl --user -u site-build.service --no-pager -n 50` for the first failing command.
- Confirm `systemctl --user list-timers --all site-build.timer` shows a next run.
- After changing a unit, run `systemctl --user daemon-reload`; stop and start the timer when changing its deadline.
- A build only publishes existing source unless its service explicitly runs your generator first.

For another self-contained timer example, see [the systemd timer card](../../commands/systemd-timer.md).
