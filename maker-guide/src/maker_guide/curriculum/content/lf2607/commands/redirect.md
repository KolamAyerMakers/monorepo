# Command Form: `>`

## Use

```bash
work=$(mktemp -d)
printf 'hello makers\n' > "$work/hi.txt"
```

## What It Does

`>` sends stdout to a file, replacing that file if it already exists.

## Practice

```bash
printf 'first\n' > "$work/hi.txt"
printf 'second\n' > "$work/hi.txt"
cat "$work/hi.txt"
```

Only `second` remains because `>` overwrites.

## Watch Out

Use `>>` when previous content must survive. Use `2>` for stderr.

The shell opens/truncates the destination **before** starting the command. Never read and overwrite the same file with `command FILE > FILE`; use a separate output path.

## Docs Pointers

- Read [append redirection](append-redirection.md), [stderr redirection](stderr-redirect.md), [I/O](../concepts/io.md), [file descriptors](../concepts/file-descriptor.md), and [stream redirection](../concepts/stream-redirection.md).
