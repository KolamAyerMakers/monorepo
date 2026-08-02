# Command: `cp`

## Use

```bash
cp source.txt copy.txt
```

## What It Does

`cp` copies files or directory trees.

## Common Forms

Copy one file:

```bash
cp ~/src/pages/index.md ~/playground/index.backup.md
```

Copy into a directory:

```bash
cp notes.md ~/playground/
```

Copy a directory tree recursively:

```bash
cp -r ~/src/pages ~/playground/pages-backup
```

Prompt before overwriting:

```bash
cp -i source.txt target.txt
```

## Watch Out

`cp` can overwrite existing files. Use `cp -i` when practicing. Use `cp -r` only when you intend to copy a directory tree.

## Docs Pointers

- Run `man cp`.
- Read [file](../concepts/file.md), [directory](../concepts/directory.md), and [path](../concepts/path.md).
