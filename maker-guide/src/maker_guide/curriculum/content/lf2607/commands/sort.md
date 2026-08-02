# sort

## Use

```bash
sort names.txt
```

## What It Does

`sort` orders lines of text and prints the ordered result.

## Common Forms

Sort a file:

```bash
sort names.txt
```

Sort pipeline output:

```bash
grep makers ~/src/pages/*.md | sort
```

Sort uniquely:

```bash
sort -u names.txt
```

Sort numerically:

```bash
sort -n numbers.txt
```

Reverse the order with `-r`. Combine it with numeric sorting to rank counts from largest to smallest:

```bash
sort -nr counts.txt
```

## `sort -u` Versus `uniq`

`sort -u` sorts and removes duplicate lines in one command.

`uniq` only removes adjacent duplicate lines, so it usually needs sorted input first:

```bash
sort names.txt | uniq
```

Use `sort -u` when you only need unique sorted lines. Use `sort | uniq -c` when you need counts.

## Docs Pointers

- Run `man sort`.
- Read [uniq](uniq.md), [pipes](../concepts/pipes.md), and [one-liners](../concepts/oneliner.md).
