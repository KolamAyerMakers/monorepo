# bzip2

## Use

```bash
bzip2 -d file.bz2
```

## What It Does

`bzip2` compresses or decompresses bzip2 files.

It is another compression format. Use `file` to decide whether data is bzip2 before choosing this tool.

## Practice

Use it when `file` reports bzip2-compressed data.

## Watch Out

Do not assume every compressed file is gzip. Ask `file` first.

## Docs Pointers

- Run `man bzip2`.
- Read [File Compression And Archives](../concepts/file-compression.md).
