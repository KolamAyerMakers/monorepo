#!/bin/bash

mkdir -p "$HOME/playground/singapore" "$HOME/src/pages"
weather_url='https://api.open-meteo.com/v1/forecast?latitude=1.32411&longitude=103.8698&daily=temperature_2m_max,precipitation_probability_max,sunrise,sunset&timezone=Asia%2FSingapore&forecast_days=1'
air_url='https://air-quality-api.open-meteo.com/v1/air-quality?latitude=1.32411&longitude=103.8698&current=pm2_5&timezone=Asia%2FSingapore&domains=cams_global'
curl -fsS --max-time 15 "$weather_url" -o "$HOME/playground/singapore/weather.json" || exit 1
curl -fsS --max-time 15 "$air_url" -o "$HOME/playground/singapore/air.json" || exit 1

retrieved=$(date)

# TODO 1: Assign forecast_date, temperature, rain, sunrise, sunset, air_time,
# and pm25 using jq -r and command substitution on weather.json and air.json.
# TODO 2: Use printf to write the bulletin to "$HOME/src/pages/today.md".
# EXERCISE_INCOMPLETE
