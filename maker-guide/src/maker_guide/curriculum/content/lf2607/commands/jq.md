# jq

`jq` reads JSON and selects or transforms values using a filter. It writes JSON by default; `-r` prints strings without JSON quotes.

## Example

Create a small input and select a nested field:

```bash
printf '%s\n' '{"forecast":{"maximum":31.5,"unit":"°C"}}' > forecast.json
jq '.forecast.maximum' forecast.json
jq -r '.forecast.unit' forecast.json
```

The first filter outputs a JSON number; the second outputs plain text. Array indexes such as `[0]` select the first element. Use `jq -e` when a filter's truth value should affect the command's exit status.

## Related Reading

- [Files and data](../concepts/file.md)
- [shell variables](../concepts/variables.md)
