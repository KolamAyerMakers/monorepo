# uniq

## Use

```bash
printf 'Ada\nLinus\nAda\n' | sort | uniq
```

## What It Does

`uniq` removes adjacent duplicate lines.

## Examples

Collapse duplicates after sorting:

```bash
printf 'Ada\nLinus\nAda\n' | sort | uniq
```

Count duplicates:

```bash
printf 'Ada\nLinus\nAda\n' | sort | uniq -c
```

Show only duplicate lines:

```bash
printf 'Ada\nLinus\nAda\n' | sort | uniq -d
```

## Watch Out

If duplicates are not next to each other, `uniq` will not remove them. That is why `sort | uniq` is common.

## Docs Pointers

- Run `man uniq`.
- Read [sort](sort.md), [pipes](../concepts/pipes.md), and [text search](../concepts/text-search.md).
