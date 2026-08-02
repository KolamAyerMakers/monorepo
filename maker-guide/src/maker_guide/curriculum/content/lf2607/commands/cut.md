# cut

## Use

```bash
cut -d: -f1 /etc/passwd
```

## What It Does

`cut` extracts columns from each line.

## Practice

Use `-d` for the delimiter and `-f` for the field number.

## Watch Out

`cut` is simple. If the data has quoting or nested structure, use a better parser later.
