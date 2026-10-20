# File Compression And Archives

## Core Idea

An archive groups files. Compression makes bytes smaller. These are related but not the same. A `.tar` file is usually an archive. `.gz` and `.bz2` are compression formats. A `.tar.gz` file is both: tar archive first, gzip compression around it.

## Identify First

Run `file PATH`, replacing `PATH` with the file you are investigating. Do not choose the decoder solely from its filename: extensions can be wrong.

## Safe Archive Workflow

The [tar card](../commands/tar.md) creates a small archive and an empty extraction directory. Follow that example before trying an unfamiliar archive. List paths before extraction, use a new directory without sudo, and do not execute extracted files merely because extraction succeeded. A scratch directory is not a sandbox for malicious content.

## Compression Workflow

The [gzip](../commands/gzip.md) and [bzip2](../commands/bzip2.md) cards introduce their own input files. Their `-dc` examples decode to stdout without replacing the compressed input. Plain decompression commonly replaces its input; preserve originals when investigating.

## Common Confusions

- `tar` does not mean compression by itself.
- `gzip` and `bzip2` usually handle one byte stream, not a tree of files.
- `base64` is encoding, not encryption and not compression.
- `file` is a strong hint, not an oracle.

## Proof Check

Given an unknown file, run `file` first, choose the next command, and write down why that command fits the reported type.

## Docs Pointers

- Run `man file`, `man tar`, `man gzip`, `man bzip2`, and `man base64`.
- Read the GNU tar manual section on [operations](https://www.gnu.org/software/tar/manual/html_node/Operations.html).
