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

Fetch a one-day forecast and current air-quality estimate for Singapore with the free Open-Meteo APIs. The forecast's maximum temperature is a forecast, not the current temperature. The air value is CAMS model data, not Singapore's official PSI or a local-station reading; this page gives no health advice.

Inspect the weather JSON before extracting a field. `daily.temperature_2m_max` is an array because the response can contain several forecast days; `[0]` selects the first day. For this number, `jq -r '.daily.temperature_2m_max[0]'` prints the same value as normal `jq`; `-r` removes JSON quotation marks from strings. Then inspect the air response and select `current.pm2_5`.

The complete starter below retrieves both documents, checks required values and units, and only then replaces `~/src/pages/singapore-today.md`. It publishes only checked numeric values and dates, not arbitrary response text. Both temporary files and the output temporary file are removed on failure; the prior page remains in place.

Create the file first:

```bash
mkdir -p ~/scripts
micro ~/scripts/singapore-today.sh
```

Create `~/scripts/singapore-today.sh`:

Paste the complete script below into the editor, then save the file:

```bash
#!/usr/bin/env bash
set -euo pipefail

output="$HOME/src/pages/singapore-today.md"
weather=$(mktemp)
air=$(mktemp)
temporary=$(mktemp "$HOME/src/pages/.singapore-today.XXXXXX")
trap 'rm -f "$weather" "$air" "$temporary"' EXIT

curl --max-time 15 -fsS 'https://api.open-meteo.com/v1/forecast?latitude=1.3521&longitude=103.8198&daily=temperature_2m_max,precipitation_probability_max,sunrise,sunset&timezone=Asia%2FSingapore&forecast_days=1' -o "$weather"
curl --max-time 15 -fsS 'https://air-quality-api.open-meteo.com/v1/air-quality?latitude=1.3521&longitude=103.8198&current=pm2_5&timezone=Asia%2FSingapore&domains=cams_global' -o "$air"

jq -e '
  .daily.time[0] | strings | test("^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
' "$weather" >/dev/null
jq -e '
  (.daily.temperature_2m_max[0] | numbers) as $temperature |
  (.daily.precipitation_probability_max[0] | numbers) as $rain |
  (.daily.sunrise[0] | strings | test("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}$")) and
  (.daily.sunset[0] | strings | test("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}$")) and
  ($temperature >= -100 and $temperature <= 70) and ($rain >= 0 and $rain <= 100) and
  .daily_units.temperature_2m_max == "°C" and
  .daily_units.precipitation_probability_max == "%"
' "$weather" >/dev/null
jq -e '
  (.current.pm2_5 | numbers) as $pm |
  (.current.time | strings | test("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}$")) and
  ($pm >= 0 and $pm <= 1000) and .current_units.pm2_5 == "μg/m³"
' "$air" >/dev/null

forecast_date=$(jq -r '.daily.time[0]' "$weather")
temperature=$(jq -r '.daily.temperature_2m_max[0]' "$weather")
rain=$(jq -r '.daily.precipitation_probability_max[0]' "$weather")
sunrise=$(jq -r '.daily.sunrise[0]' "$weather")
sunset=$(jq -r '.daily.sunset[0]' "$weather")
air_time=$(jq -r '.current.time' "$air")
pm25=$(jq -r '.current.pm2_5' "$air")

for calendar_value in "$forecast_date" "${sunrise%T*}" "${sunset%T*}"; do
  parsed_date=$(TZ=Asia/Singapore date -d "$calendar_value" +%F 2>/dev/null) || exit 1
  [[ "$parsed_date" == "$calendar_value" ]] || exit 1
done
for clock_value in "$sunrise" "$sunset" "$air_time"; do
  parsed_clock=$(TZ=Asia/Singapore date -d "$clock_value" '+%Y-%m-%dT%H:%M' 2>/dev/null) || exit 1
  [[ "$parsed_clock" == "$clock_value" ]] || exit 1
done
retrieved=$(TZ=Asia/Singapore date --iso-8601=seconds)

cat >"$temporary" <<EOF
# Singapore Today

Forecast date: $forecast_date (Asia/Singapore)

- Forecast maximum temperature: $temperature °C
- Maximum precipitation probability: $rain %
- Sunrise: $sunrise (Asia/Singapore)
- Sunset: $sunset (Asia/Singapore)
- Modelled PM2.5: $pm25 μg/m³ (CAMS; model timestamp $air_time Asia/Singapore)

Retrieved: $retrieved

Weather forecast: [Open-Meteo](https://open-meteo.com/)
Air-quality model: [CAMS via Open-Meteo](https://open-meteo.com/en/docs/air-quality-api)
EOF
mv "$temporary" "$output"
```

Make it executable with `chmod +x ~/scripts/singapore-today.sh`, run it, and inspect `~/src/pages/singapore-today.md`. Add `[Singapore today](singapore-today.html)` to `~/src/pages/index.md`. The generated page is overwritten on each successful run.

Add this line to `[Service]` before `ExecStart`:

```ini
ExecStartPre=/bin/bash %h/scripts/singapore-today.sh
```

The pre-start generator runs before each build. If either API request or validation fails, it exits without replacing the last good source page, and systemd does not proceed to the build. Reload the units, run the service, inspect its journal, and check `/singapore-today.html`. This is scheduled static content: the server builds a new page; visitors' browsers do not generate it.

Prove the automatic path without waiting for tomorrow: first run the daily service and confirm `/singapore-today.html` is published. Personalize its page heading in the script's Markdown template; do not edit the generated page. Stop the timer and wait for any build to finish. Temporarily replace `OnCalendar` with `OnActiveSec=30s`, reload, inspect the effective unit with `systemctl --user cat site-build.timer`, and start it. Wait for a new journal activation and verify your heading and a new retrieval timestamp at `/singapore-today.html`; do not manually run the generator or build during this proof. Stop the timer, restore `OnCalendar=*-*-* 09:00:00`, reload, inspect, restart the timer, and check its next deadline.

Make the page feel like yours, and leave the normal daily 09:00 schedule active when done.

## If It Does Not Work

- Read `journalctl --user -u site-build.service --no-pager -n 50` for the first failing command.
- Confirm `systemctl --user list-timers --all site-build.timer` shows a next run.
- After changing a unit, run `systemctl --user daemon-reload`; stop and start the timer when changing its deadline.
- A build only publishes existing source unless its service explicitly runs your generator first.

For another self-contained timer example, see [the systemd timer card](../../commands/systemd-timer.md).
