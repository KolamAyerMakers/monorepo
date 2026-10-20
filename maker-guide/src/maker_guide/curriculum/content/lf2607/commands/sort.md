# sort

## Use

```bash
printf 'Linus\nAda\nAda\n' | sort
```

## What It Does

`sort` orders lines of text and prints the ordered result.

## Common Forms

Sort a file:

```bash
printf 'Linus\nAda\nAda\n' | sort
```

Sort pipeline output:

```bash
cut -d: -f7 /etc/passwd | sort
```

Sort uniquely:

```bash
printf 'Linus\nAda\nAda\n' | sort -u
```

Sort numerically:

```bash
printf '10\n2\n1\n' | sort -n
```

Reverse the order with `-r`. Combine it with numeric sorting to rank counts from largest to smallest:

```bash
printf '10\n2\n1\n' | sort -nr
```

## `sort -u` Versus `uniq`

`sort -u` sorts and removes duplicate lines in one command.

`uniq` only removes adjacent duplicate lines, so it usually needs sorted input first:

```bash
printf 'Linus\nAda\nAda\n' | sort | uniq
```

Use `sort -u` when you only need unique sorted lines. Use `sort | uniq -c` when you need counts.

## Docs Pointers

- Run `man sort`.
- Read [uniq](uniq.md), [pipes](../concepts/pipes.md), and [one-liners](../concepts/oneliner.md).
