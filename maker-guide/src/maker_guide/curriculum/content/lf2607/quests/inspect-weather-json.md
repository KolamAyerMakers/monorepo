# Inspect a weather snapshot

Quest: inspect-weather-json

## Mission

Save one Open-Meteo weather JSON response at `~/playground/singapore/weather.json` and inspect its daily forecast fields and units with `jq`.

## Commands You Will Use

- `curl`
- `jq`

## Steps

1. Create `~/playground/singapore` and save the weather response as `weather.json`.
2. Use `jq` to inspect the daily date, maximum temperature, and units.
3. Leave the saved response for the next exercise.

The maximum is a forecast in °C, not the current temperature.

## Hints

1. `jq` reads JSON fields using a filter.

## Related Reading

- [jq](../commands/jq.md)
- [S9 self-study](../sessions/S09/self-study.md)
