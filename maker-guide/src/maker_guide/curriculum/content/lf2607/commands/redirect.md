# Command Form: `>`

## Use

```bash
printf 'hello makers\n' > ~/playground/hi.txt
```

## What It Does

`>` sends stdout to a file, replacing that file if it already exists.

## Practice

```bash
printf 'first\n' > ~/playground/hi.txt
printf 'second\n' > ~/playground/hi.txt
cat ~/playground/hi.txt
```

Only `second` remains because `>` overwrites.

## Watch Out

Use `>>` when previous content must survive. Use `2>` for stderr.

## Docs Pointers

- Read [append redirection](append-redirection.md), [stderr redirection](stderr-redirect.md), [I/O](../concepts/io.md), [file descriptors](../concepts/file-descriptor.md), and [stream redirection](../concepts/stream-redirection.md).
