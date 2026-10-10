# Keep Your Website Up To Date

Session: S9

2026-10-10

Your website can update itself while you are away.

<!-- end_slide -->

# Services And Timers

- `site.service` serves your published website.
- `site-build.service` builds it once.
- `site-build.timer` schedules that build.

**A service defines the task. A timer defines when it runs.**

<!-- end_slide -->

# More Than "Run Every Day"

- Run every morning or every Monday.
- Run five minutes after the timer is activated.
- Wait ten minutes after the job finishes before running again.
- With `Persistent=true`, if the computer was off for three scheduled runs, schedule one catch-up run when the timer starts again.

<!-- end_slide -->

# First, Build The Site Once

Save as `~/.config/systemd/user/site-build.service`:

```ini
[Unit]
Description=Build my website

[Service]
Type=oneshot
WorkingDirectory=%h/src
ExecStart=/usr/local/bin/maker-guide-build-personal-website
```

`Type=oneshot` means systemd waits for this finite task to finish.

```bash
systemctl --user daemon-reload
systemctl --user start site-build.service
journalctl --user -u site-build.service
```

Check the journal for a successful build. A completed oneshot normally shows inactive; that is expected.

<!-- end_slide -->

# Now Say When: Every Hour

Save as `~/.config/systemd/user/site-build.timer`:

```ini
[Unit]
Description=Build my website every hour

[Timer]
OnCalendar=hourly
RandomizedDelaySec=55min

[Install]
WantedBy=timers.target
```

The matching name makes this timer start `site-build.service`. The random delay spreads builds across the hour.

<!-- end_slide -->

# Read The Calendar

`OnCalendar=hourly` sets an event at each clock hour. `RandomizedDelaySec=55min` adds up to 55 minutes before the build. Ask systemd to explain the next calendar occurrence:

```bash
systemd-analyze calendar hourly
```

<!-- end_slide -->

# Read The Next Run

Example: Saturday 10 October 2026, 13:00 (+08).

```text
$ date
Sat Oct 10 13:00:00 +08 2026

$ systemd-analyze calendar hourly
Normalized form: *-*-* *:00:00
    Next elapse: Sat 2026-10-10 14:00:00 +08
       (in UTC): Sat 2026-10-10 06:00:00 UTC
       From now: 1h left
```

The next calendar event is 14:00 UTC+08 (06:00 UTC), in one hour. The random delay makes the actual start approximately 14:00–14:55, subject to timer accuracy.

<!-- end_slide -->

# Make The Hourly Schedule Active

```bash
systemctl --user enable --now site-build.timer
systemctl --user list-timers --all site-build.timer
```

The timer listing shows the next scheduled time, not proof a build succeeded. The journal shows what happened. A user timer also depends on the user manager being available.

<!-- end_slide -->

# Hourly Website Build — Recap

Create `~/.config/systemd/user/site-build.service`:

```ini
[Service]
Type=oneshot
WorkingDirectory=%h/src
ExecStart=/usr/local/bin/maker-guide-build-personal-website
```

Create `~/.config/systemd/user/site-build.timer`:

```ini
[Timer]
OnCalendar=hourly
RandomizedDelaySec=55min
[Install]
WantedBy=timers.target
```

Activate and verify the hourly build:

```bash
systemctl --user daemon-reload
systemctl --user start site-build.service
journalctl --user -u site-build.service
systemctl --user enable --now site-build.timer
systemctl --user list-timers --all site-build.timer
```

<!-- end_slide -->

# Singapore Today

Build a **Singapore Today** page on your website showing:

- Today's forecast maximum temperature and rain probability
- Sunrise and sunset
- Modelled PM2.5
- Data sources and retrieval time

Update it automatically every hour, with a randomized start delay of up to 55 minutes.

<!-- end_slide -->

# JSON Data Has Structure

JSON stores data as keys and values. This illustrative forecast fragment is not live data:

```json
{
  "daily": {
    "time": ["2026-10-10"],
    "temperature_2m_max": [31.5]
  }
}
```

- `{}` is an object containing named keys and values.
- `[]` is an ordered array; here it contains one forecast day.
- Dates are quoted strings; `31.5` is a number.

<!-- end_slide -->

# Read JSON From The Command Line

`jq` formats JSON and can extract a value. This filter selects the `temperature` field:

```bash
echo '{"temperature":31.5}' | jq '.temperature'
```

The pipe feeds JSON to `jq`; the filter prints the selected JSON value:

```text
31.5
```

<!-- end_slide -->

# Fetch Forecast JSON

Open-Meteo returns JSON for Singapore. Fetch and inspect the response:

```bash
weather_url='https://api.open-meteo.com/v1/forecast?'
weather_url+='latitude=1.32411'
weather_url+='&longitude=103.8698'
weather_url+='&daily=temperature_2m_max'
weather_url+=',precipitation_probability_max'
weather_url+=',sunrise,sunset'
weather_url+='&timezone=Asia%2FSingapore'
weather_url+='&forecast_days=1'
curl --max-time 15 -fsS "$weather_url" -o /tmp/weather.json
jq . /tmp/weather.json
```

<!-- end_slide -->

# Extract One Forecast Value

Illustrative response fragment (not live forecast data):

```json
{"daily":{"temperature_2m_max":[31.5,30.8]}}
```

The field is an array of forecast days; `[0]` selects the first day's forecast maximum, not the current temperature.

```bash
jq -r '.daily.temperature_2m_max[0]' /tmp/weather.json
```

Here `-r` prints the number unchanged; for strings it removes JSON quotation marks.

<!-- end_slide -->

# Fetch Modelled Air Quality

`current.pm2_5` is a separate CAMS model estimate, not official PSI or a local-station reading:

```bash
air_url='https://air-quality-api.open-meteo.com/v1/air-quality'
air_url+='?latitude=1.32411'
air_url+='&longitude=103.8698'
air_url+='&current=pm2_5'
air_url+='&timezone=Asia%2FSingapore'
air_url+='&domains=cams_global'
curl --max-time 15 -fsS "$air_url" -o /tmp/air.json
jq -r '.current.pm2_5' /tmp/air.json
```

<!-- end_slide -->

# From JSON To Markdown

This standalone terminal example reads a JSON title and writes a Markdown file:

```bash
title=$(echo '{"title":"Dune"}' | jq -r '.title')
printf '# Reading\n\nBook: %s\n' "$title" > /tmp/reading.md
cat /tmp/reading.md
```

`$()` captures output, `-r` removes JSON string quotes, `%s` inserts the value, `\n` adds a line break, and `>` writes the file.

<!-- end_slide -->

# Complete The Generator

Copy the starter and edit it:

```bash
mkdir -p ~/scripts
cp /docs/sessions/S09/resources/today.sh \
    ~/scripts/today.sh
micro ~/scripts/today.sh
```

Adapt the technique to extract every required field in TODO 1 and write the full attributed report in TODO 2. Only when both are complete, remove the `EXERCISE_INCOMPLETE` comment, diagnostic, and `exit 1`.

Then run it and inspect `~/src/pages/today.md`:

```bash
bash ~/scripts/today.sh
```

<!-- end_slide -->

# Schedule And Verify

Insert `ExecStartPre` before the existing `ExecStart` in `site-build.service`:

```ini
ExecStartPre=/bin/bash %h/scripts/today.sh
ExecStart=/usr/local/bin/maker-guide-build-personal-website
```

Link the page from your homepage, then reload and manually test the service:

```bash
systemctl --user daemon-reload
systemctl --user start site-build.service
```

Check the published page’s fields and retrieval time, then enable the hourly timer and check its next scheduled run.

```bash
systemctl --user daemon-reload
systemctl --user enable --now site-build.timer
systemctl --user list-timers --all site-build.timer
```

<!-- end_slide -->

# See You On 24 October

S10 is our final session — 24 October 2026.

- We will discuss how to keep learning after Linux Foundations.
- Then we will celebrate at the graduation ceremony, with certificates and a small gift.
