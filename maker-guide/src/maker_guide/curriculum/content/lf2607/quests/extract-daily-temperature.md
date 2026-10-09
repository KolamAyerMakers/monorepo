# Extract the daily maximum

Quest: extract-daily-temperature

## Mission

Use `jq` to write the numeric forecast maximum from the saved weather snapshot to `~/playground/singapore/temperature.txt`.

## Commands You Will Use

- `jq`
- `printf`
- `>`

## Steps

1. Read the saved JSON from the previous exercise.
2. Select its first daily maximum and save only the number in `~/playground/singapore/temperature.txt`.
3. Compare the saved value with the source snapshot.

## Hints

1. The daily forecast maximum is an array value.

## Related Reading

- [jq](../commands/jq.md)
- [S9 self-study](../sessions/S09/self-study.md)
