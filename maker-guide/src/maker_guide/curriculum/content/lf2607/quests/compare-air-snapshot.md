# Compare air-quality data

Quest: compare-air-snapshot

## Mission

Save an Open-Meteo air-quality response as `~/playground/singapore/air.json`. Record its modelled PM2.5 value and current model timestamp in `~/playground/singapore/air.txt`.

## Commands You Will Use

- `curl`
- `jq`
- `printf`

## Steps

1. Save the CAMS-domain response in `air.json`.
2. Record these labelled lines in `~/playground/singapore/air.txt`: `PM2.5: <value> μg/m³` and `Model time: <timestamp>`.
3. Compare both values with the JSON response.

This is CAMS model data in μg/m³, not official PSI or a local-station reading.

## Hints

1. The value and timestamp are both under `current`.
2. Keep the API timestamp in ISO format.

## Related Reading

- [jq](../commands/jq.md)
- [S9 self-study](../sessions/S09/self-study.md)
