# tar

## Use

```bash
work=$(mktemp -d)
printf 'hello\n' > "$work/note.txt"
tar -cf "$work/notes.tar" -C "$work" note.txt
tar -tf "$work/notes.tar"
mkdir "$work/extracted"
tar -xf "$work/notes.tar" -C "$work/extracted"
cat "$work/extracted/note.txt"
```

## What It Does

`tar` creates (`-c`), lists (`-t`), or extracts (`-x`) archives. `-f` selects the archive file; `-C` selects the working directory for the following operation.

Tar archives group paths into one file. Tar by itself is not compression, though tar archives are often compressed afterward.

## Practice

List with `-t` before extracting with `-x`.

## Watch Out

The example lists `note.txt` and prints `hello` after extraction. For other archives, list first and extract into a **new empty directory** without sudo. Paths, symlinks, and existing destination files deserve inspection; a scratch directory is not a security sandbox for a malicious archive.

## Recovery

- List before extracting: `tar -tf archive.tar`.
- Extract into a new directory: `mkdir extract && tar -xf archive.tar -C extract`.
- If `tar` says the file is not a tar archive, run `file archive.tar` before guessing again.

## Docs Pointers

- Run `man tar`.
- Read [File Compression And Archives](../concepts/file-compression.md).
- Read the GNU tar manual on [operations](https://www.gnu.org/software/tar/manual/html_node/Operations.html).
