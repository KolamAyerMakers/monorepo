# File Compression And Archives

## Core Idea

An archive groups files. Compression makes bytes smaller. These are related but not the same. A `.tar` file is usually an archive. `.gz` and `.bz2` are compression formats. A `.tar.gz` file is both: tar archive first, gzip compression around it.

## Always Identify First

```bash
file unknown
```

Do not guess the decoder from the filename. Filenames can lie, especially in puzzles.

## Safe Archive Workflow

```bash
mkdir -p ~/extract-work
tar -tf archive.tar
tar -xf archive.tar -C ~/extract-work
find ~/extract-work -maxdepth 2 -type f -print
```

List before extracting. Extract into a scratch directory so an archive cannot spray files across your current workspace.

## Compression Workflow

```bash
gzip -d file.gz
bzip2 -d file.bz2
base64 -d encoded.txt > decoded.bin
```

Decompression tools often replace the compressed file with the decompressed output. Work on copies when experimenting.

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
