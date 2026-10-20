# grep

## Use

```bash
grep -n ssh /etc/services
```

## What It Does

`grep` prints lines that match text or a regular expression pattern.

## Practice

Use `grep -n word file` to show matching line numbers. Pipe matching output into another tool when you want a summary:

```bash
grep ssh /etc/services | wc -l
```

Recursive directory search is later material. `-r` descends through subdirectories; `-R` also follows symbolic links, so use either only when you understand the tree being searched.

## Optional Exploration

Regex anchors are optional exploration for later. They restrict a match to a position in the line:

```bash
grep '^#' /etc/services
```

## Watch Out

Quote patterns that contain spaces or shell characters.

Use `-F` for literal text rather than regex. Exit status `0` means a match, `1` means no match, and `2` means an error; empty output alone does not distinguish them.

## Docs Pointers

- Run `man grep`.
- Read [Regular Expression](../concepts/regular-expression.md).
- Read [Text Search](../concepts/text-search.md).
