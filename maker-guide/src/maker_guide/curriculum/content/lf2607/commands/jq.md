# jq

`jq` reads JSON and selects or transforms values using a filter. It writes JSON by default; `-r` prints strings without JSON quotes.

## Example

Create a small input and select a nested field:

```bash
work=$(mktemp -d)
printf '%s\n' '{"forecast":{"maximum":31.5,"unit":"°C"}}' > "$work/forecast.json"
jq '.forecast.maximum' "$work/forecast.json"
jq -r '.forecast.unit' "$work/forecast.json"
```

Expect `31.5`, then `°C`. Array indexes such as `[0]` select the first element. An absent field commonly produces `null`, not a parsing error. Use `jq -e` to fail when the final result is `false` or `null`; validate the expected type too before using a value in a report.

## Related Reading

- [Files and data](../concepts/file.md)
- [shell variables](../concepts/variables.md)
