# gzip

## Use

```bash
gzip -d file.gz
```

## What It Does

`gzip` compresses or decompresses gzip files.

It handles one compressed byte stream. A `.tar.gz` file is a tar archive compressed with gzip.

## Practice

Use `file` first to confirm the compression type.

## Watch Out

Decompression may replace the input file with the output file.

## Docs Pointers

- Run `man gzip`.
- Read [File Compression And Archives](../concepts/file-compression.md).
