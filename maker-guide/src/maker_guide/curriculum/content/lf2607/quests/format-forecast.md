# Format a forecast note

Quest: format-forecast

## Mission

Use a shell variable and `printf` to write `~/playground/singapore/forecast.md` with the maximum temperature from your saved snapshot and its °C unit.

## Commands You Will Use

- `jq`
- `printf`
- `>`

## Steps

1. Read the saved maximum into a shell variable.
2. Write a heading and a `Maximum: <value> °C` line in the note.
3. Compare its numeric value with the JSON snapshot.

Keep the snapshot's exact numeric value; trailing zeros are fine (for example, `31.5` or `31.50`).

## Hints

1. Shell command substitution stores a command's output in a variable.

## Related Reading

- [jq](../commands/jq.md)
- [S9 self-study](../sessions/S09/self-study.md)
