# tar

## Use

```bash
tar -tf archive.tar
```

## What It Does

`tar` lists or extracts tar archives.

Tar archives group paths into one file. Tar by itself is not compression, though tar archives are often compressed afterward.

## Practice

List with `-t` before extracting with `-x`.

## Watch Out

Archives can contain paths. Extract into a scratch directory first.

## Recovery

- List before extracting: `tar -tf archive.tar`.
- Extract into a scratch directory: `mkdir -p extract && tar -xf archive.tar -C extract`.
- If `tar` says the file is not a tar archive, run `file archive.tar` before guessing again.

## Docs Pointers

- Run `man tar`.
- Read [File Compression And Archives](../concepts/file-compression.md).
- Read the GNU tar manual on [operations](https://www.gnu.org/software/tar/manual/html_node/Operations.html).
