#!/bin/bash
# Complete S9 reference: preserve the last good bulletin on download/data failure.
set -euo pipefail

mkdir -p "$HOME/playground/singapore" "$HOME/src/pages"
temporary_directory=$(mktemp -d "$HOME/playground/singapore/.today.XXXXXX")
temporary_page=$(mktemp "$HOME/src/pages/.today.XXXXXX")
trap 'rm -rf -- "$temporary_directory"; rm -f -- "$temporary_page"' EXIT

weather_url='https://api.open-meteo.com/v1/forecast?latitude=1.32411&longitude=103.8698&daily=temperature_2m_max,precipitation_probability_max,sunrise,sunset&timezone=Asia%2FSingapore&forecast_days=1'
air_url='https://air-quality-api.open-meteo.com/v1/air-quality?latitude=1.32411&longitude=103.8698&current=pm2_5&timezone=Asia%2FSingapore&domains=cams_global'
curl -fsS --max-time 15 "$weather_url" -o "$temporary_directory/weather.json"
curl -fsS --max-time 15 "$air_url" -o "$temporary_directory/air.json"

# -e rejects missing/null fields; type checks prevent publishing error payloads.
forecast_date=$(jq -er '.daily.time[0] | select(type == "string" and length > 0)' "$temporary_directory/weather.json")
temperature=$(jq -er '.daily.temperature_2m_max[0] | select(type == "number")' "$temporary_directory/weather.json")
rain=$(jq -er '.daily.precipitation_probability_max[0] | select(type == "number" and . >= 0 and . <= 100)' "$temporary_directory/weather.json")
sunrise=$(jq -er '.daily.sunrise[0] | select(type == "string" and length > 0)' "$temporary_directory/weather.json")
sunset=$(jq -er '.daily.sunset[0] | select(type == "string" and length > 0)' "$temporary_directory/weather.json")
air_time=$(jq -er '.current.time | select(type == "string" and length > 0)' "$temporary_directory/air.json")
pm25=$(jq -er '.current.pm2_5 | select(type == "number" and . >= 0)' "$temporary_directory/air.json")
retrieved=$(date)

{
  printf '# Singapore today\n\nLocation: 1.32411, 103.8698 — Asia/Singapore\n\n'
  printf '## Forecast\n\n'
  printf '* Date: %s\n* Maximum: %s °C\n* Rain probability: %s%%\n' "$forecast_date" "$temperature" "$rain"
  printf '* Sunrise: %s\n* Sunset: %s\n\n' "$sunrise" "$sunset"
  printf '## Air quality\n\n* Model time: %s\n* PM2.5: %s μg/m³\n\n' "$air_time" "$pm25"
  printf 'PM2.5 is modelled, not a station reading or official Singapore PSI.\n'
  printf 'Forecast and model times are in Singapore time.\n\nRetrieved: %s\n\n' "$retrieved"
  printf 'Sources: Open-Meteo weather forecast; CAMS Global air-quality model via Open-Meteo.\n'
} > "$temporary_page"

mv -- "$temporary_directory/weather.json" "$HOME/playground/singapore/weather.json"
mv -- "$temporary_directory/air.json" "$HOME/playground/singapore/air.json"
chmod 644 "$temporary_page"
mv -T -- "$temporary_page" "$HOME/src/pages/today.md"
