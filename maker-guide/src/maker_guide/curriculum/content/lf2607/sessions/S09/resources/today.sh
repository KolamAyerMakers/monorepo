#!/bin/bash
set -euo pipefail

output=${1:-"$HOME/src/pages/singapore-today.md"}
output_directory=$(dirname "$output")
mkdir -p "$output_directory"
report=$(mktemp "$output_directory/.singapore-today.XXXXXX")
weather_url='https://api.open-meteo.com/v1/forecast?latitude=1.32411&longitude=103.8698&daily=temperature_2m_max,precipitation_probability_max,sunrise,sunset&timezone=Asia%2FSingapore&forecast_days=1'
air_url='https://air-quality-api.open-meteo.com/v1/air-quality?latitude=1.32411&longitude=103.8698&current=pm2_5&timezone=Asia%2FSingapore&domains=cams_global'
temporary_directory=$(mktemp -d)
trap 'rm -rf "$temporary_directory"; rm -f "$report"' EXIT

for name in weather air; do
    case $name in
        weather) url=$weather_url ;;
        air) url=$air_url ;;
    esac
    if ! curl --max-time 15 -fsS "$url" -o "$temporary_directory/$name.json"; then
        echo "Could not retrieve $name data." >&2
        exit 1
    fi
done

jq -e '
  (.daily.time[0] | strings | (try (strptime("%Y-%m-%d") | length == 8) catch false)) and
  (.daily.temperature_2m_max[0] | numbers | . >= -100 and . <= 70) and
  (.daily.precipitation_probability_max[0] | numbers | . >= 0 and . <= 100) and
  (.daily.sunrise[0] | strings | (try (strptime("%Y-%m-%dT%H:%M") | length >= 5) catch false)) and
  (.daily.sunset[0] | strings | (try (strptime("%Y-%m-%dT%H:%M") | length >= 5) catch false)) and
  .daily_units.temperature_2m_max == "°C" and .daily_units.precipitation_probability_max == "%"
' "$temporary_directory/weather.json" >/dev/null
jq -e '
  (.current.pm2_5 | numbers | . >= 0 and . <= 1000) and
  (.current.time | strings | (try (strptime("%Y-%m-%dT%H:%M") | length >= 5) catch false)) and .current_units.pm2_5 == "μg/m³"
' "$temporary_directory/air.json" >/dev/null

for calendar_value in \
    "$(jq -r '.daily.time[0]' "$temporary_directory/weather.json")" \
    "$(jq -r '.daily.sunrise[0] | split("T")[0]' "$temporary_directory/weather.json")" \
    "$(jq -r '.daily.sunset[0] | split("T")[0]' "$temporary_directory/weather.json")"; do
    parsed_date=$(TZ=Asia/Singapore date -d "$calendar_value" +%F 2>/dev/null) || exit 1
    [[ $parsed_date == "$calendar_value" ]] || exit 1
done
for clock_value in \
    "$(jq -r '.daily.sunrise[0]' "$temporary_directory/weather.json")" \
    "$(jq -r '.daily.sunset[0]' "$temporary_directory/weather.json")" \
    "$(jq -r '.current.time' "$temporary_directory/air.json")"; do
    parsed_clock=$(TZ=Asia/Singapore date -d "$clock_value" '+%Y-%m-%dT%H:%M' 2>/dev/null) || exit 1
    [[ $parsed_clock == "$clock_value" ]] || exit 1
done

retrieved=$(TZ=Asia/Singapore date --iso-8601=seconds)

# EXERCISE_INCOMPLETE: finish the field extraction and Markdown composition exercises.
echo "EXERCISE_INCOMPLETE: complete both TODO sections before publication." >&2
exit 1

# TODO 1: assign forecast_date, temperature, rain, sunrise, sunset, air_time,
# and pm25 using jq -r and command substitution on the validated temporary JSON.
# TODO 2: compose attributed Markdown using printf and redirection into report.
# Do not label forecast PM2.5 as official PSI or a local-station measurement.
[[ -n ${forecast_date:-} && -n ${temperature:-} && -n ${rain:-} &&
   -n ${sunrise:-} && -n ${sunset:-} && -n ${air_time:-} && -n ${pm25:-} &&
   -n "$retrieved" && -s "${report:-}" ]] || {
    echo "Required report fields or output are empty." >&2
    exit 1
}
mv -- "$report" "$output"
