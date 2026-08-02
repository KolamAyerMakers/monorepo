# file

## Use

```bash
file unknown-data
```

## What It Does

`file` guesses what kind of data a path contains by inspecting bytes and metadata. It does not rely only on the filename extension.

## Practice

Use it before choosing text, archive, compression, or binary inspection tools.

```bash
file /bin/ls
file /etc/passwd
file ~/src/pages/index.md
file archive.tar.gz
```

`file` compares the beginning bytes against known signatures, checks whether bytes look like text in an encoding, and uses filesystem metadata where useful. The result is a strong hint, not a mathematical proof.

## Watch Out

File extensions are conventions, not proof.

If `file` says `ELF`, you are looking at a Linux executable or library. If it says `ASCII text` or `UTF-8 Unicode text`, text tools are usually safe.

## Docs Pointers

- Run `man file`.
- Read [file encoding](../concepts/file-encoding.md), [file](../concepts/file.md), and [number bases](../concepts/number-bases.md).
