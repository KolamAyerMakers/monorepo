# Give Your Website a Daily Update

Session: S9

2026-10-10

Your website can update itself while you are away.

<!-- end_slide -->

# A Timer Is A When, Not A What

A systemd **service** describes a task. A **timer** tells systemd when to start that service.

The task runs, finishes, and waits for its next scheduled start. No loop needs to stay running.

<!-- end_slide -->

# Finite Work Beside An Always-On Server

- `site.service` keeps serving the current website.
- `site-build.service` builds the site once, then exits.
- `site-build.timer` starts that build service on a schedule.

The web server keeps serving the site while the build runs.

<!-- end_slide -->

# More Than "Run Every Day"

- Run every morning or every Monday.
- Run five minutes after the timer is activated.
- Wait ten minutes after the job finishes before running again.
- With persistent calendar timers, catch up once when reactivated, not once for each missed run.

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

# Now Say When: Every Morning

Save as `~/.config/systemd/user/site-build.timer`:

```ini
[Unit]
Description=Build my website every morning

[Timer]
OnCalendar=*-*-* 09:00:00

[Install]
WantedBy=timers.target
```

The matching name makes this timer start `site-build.service`.

<!-- end_slide -->

# Read The Calendar

`OnCalendar=*-*-* 09:00:00` means every day at 09:00 in the server's local time zone. Without a time, a calendar event defaults to midnight.

Calendar timers are approximate, not a real-time promise. Ask systemd to explain the next occurrence:

```bash
systemd-analyze calendar '*-*-* 09:00:00'
```

Example: Saturday 10 October 2026, 13:00 (+08).

Illustrative output at that time:

```text
$ systemd-analyze calendar '*-*-* 09:00:00'
Normalized form: *-*-* 09:00:00
    Next elapse: Sun 2026-10-11 09:00:00 +08
       (in UTC): Sun 2026-10-11 01:00:00 UTC
       From now: 20h left
```

<!-- end_slide -->

# Make The Daily Schedule Active

```bash
systemctl --user enable --now site-build.timer
systemctl --user list-timers --all site-build.timer
```

The timer listing shows the next scheduled time, not proof a build succeeded. The journal shows what happened. A user timer also depends on the user manager being available.

<!-- end_slide -->

# Singapore Today

Publish a page with Singapore's daily forecast and modelled air quality. Each day, fetch JSON with `curl`, extract values with `jq`, generate Markdown with a script, then build the site with a systemd service and daily timer.

<!-- end_slide -->

# Fetch Forecast JSON

Open-Meteo returns JSON for Singapore. Fetch and inspect the response:

```bash
weather_url='https://api.open-meteo.com/v1/forecast?'
weather_url+='latitude=1.3521'
weather_url+='&longitude=103.8198'
weather_url+='&daily=temperature_2m_max,precipitation_probability_max,sunrise,sunset'
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
air_url='https://air-quality-api.open-meteo.com/v1/air-quality?latitude=1.3521&longitude=103.8198'
air_url+='&current=pm2_5&timezone=Asia%2FSingapore&domains=cams_global'
curl --max-time 15 -fsS "$air_url" -o /tmp/air.json
jq -r '.current.pm2_5' /tmp/air.json
```

<!-- end_slide -->

# Generate, Then Build

Create the script by pasting the complete [self-study starter](self-study.md#challenge-publish-singapore-conditions):

```bash
mkdir -p ~/scripts
micro ~/scripts/singapore-today.sh
```

Insert `ExecStartPre` before the existing `ExecStart` in `site-build.service`:

```ini
ExecStartPre=/bin/bash %h/scripts/singapore-today.sh
ExecStart=/usr/local/bin/maker-guide-build-personal-website
```

`ExecStartPre` generates the page before the build. Link `[Singapore today](singapore-today.html)` from your homepage. The script preserves the last good page if fetching or validation fails.

<!-- end_slide -->

# Your Challenge: Singapore Today

Use the provided complete script, connect it as `ExecStartPre`, and publish a page with a personalized presentation. Prove a short-timer activation changes that presentation and retrieval timestamp on the published page. Follow [self-study](self-study.md#challenge-publish-singapore-conditions), then restore the daily schedule.

Make the page presentation your own without changing fetched measurements. Leave the 09:00 daily schedule active when finished.
