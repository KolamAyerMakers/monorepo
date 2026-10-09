# Complete the Singapore bulletin

Quest: complete-singapore-bulletin

## Mission

Complete your copied `~/scripts/singapore-today.sh` starter and generate the complete attributed report at `~/src/pages/singapore-today.md`.

## Commands You Will Use

- `jq`
- `printf`
- `date`
- `mv`

## Steps

1. Finish the field extraction and Markdown composition in your copy of the starter.
2. Preserve its bounded fetch, JSON/unit/date validation, nonempty-field check, and atomic replacement.
3. Include labelled forecast date, maximum, rain probability, sunrise, sunset, PM2.5, model timestamp, and retrieval time, with units and Open-Meteo/CAMS attribution. Keep API dates/times in ISO format and include the retrieval timezone or UTC offset.

The starter remains incomplete; do not edit the packaged resource. A failed update must leave an existing report intact.

## Hints

1. Keep the forecast date, model timestamp, and retrieval time as distinct values.

## Related Reading

- [S9 self-study](../sessions/S09/self-study.md)
- [jq](../commands/jq.md)
