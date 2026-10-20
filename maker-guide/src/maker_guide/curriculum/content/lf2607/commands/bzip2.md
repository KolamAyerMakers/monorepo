# bzip2

## Use

```bash
work=$(mktemp -d)
printf 'hello\n' > "$work/note.txt"
bzip2 -k "$work/note.txt"
file "$work/note.txt.bz2"
bzip2 -dc "$work/note.txt.bz2"
```

## What It Does

`bzip2` compresses or decompresses bzip2 files.

It is another compression format. Use `file` to decide whether data is bzip2 before choosing this tool.

## Practice

Use it when `file` reports bzip2-compressed data.

## Watch Out

`-k` keeps the input; `-dc` decodes to stdout without replacing a file. Plain compression/decompression normally replaces its input. Do not assume every compressed file is gzip: ask `file` first.

## Docs Pointers

- Run `man bzip2`.
- Read [File Compression And Archives](../concepts/file-compression.md).
