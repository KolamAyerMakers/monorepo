# uniq

## Use

```bash
sort names.txt | uniq
```

## What It Does

`uniq` removes adjacent duplicate lines.

## Examples

Collapse duplicates after sorting:

```bash
sort names.txt | uniq
```

Count duplicates:

```bash
sort names.txt | uniq -c
```

Show only duplicate lines:

```bash
sort names.txt | uniq -d
```

## Watch Out

If duplicates are not next to each other, `uniq` will not remove them. That is why `sort | uniq` is common.

## Docs Pointers

- Run `man uniq`.
- Read [sort](sort.md), [pipes](../concepts/pipes.md), and [text search](../concepts/text-search.md).
