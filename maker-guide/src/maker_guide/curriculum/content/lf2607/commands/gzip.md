# gzip

## Use

```bash
work=$(mktemp -d)
printf 'hello\n' > "$work/note.txt"
gzip -k "$work/note.txt"
file "$work/note.txt.gz"
gzip -dc "$work/note.txt.gz"
```

## What It Does

`gzip` compresses or decompresses gzip files.

It handles one compressed byte stream. A `.tar.gz` file is a tar archive compressed with gzip.

## Practice

Use `file` first to confirm the compression type.

## Watch Out

The example keeps the input with `-k` and decodes to stdout with `-dc`, so both files survive. Plain `gzip FILE` or `gzip -d FILE.gz` normally replaces its input. Use `-dc` when you only want to inspect it.

## Docs Pointers

- Run `man gzip`.
- Read [File Compression And Archives](../concepts/file-compression.md).
