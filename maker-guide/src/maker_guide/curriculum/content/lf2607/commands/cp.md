# Command: `cp`

## Use

```bash
work=$(mktemp -d)
printf 'original\n' > "$work/source.txt"
cp -i "$work/source.txt" "$work/copy.txt"
cat "$work/copy.txt"
```

## What It Does

`cp` copies files or directory trees.

## Common Forms

The example creates a fresh temporary directory and prints `original` from the copy. Use its `work` variable for these variations.

Copy one file to another name:

```bash
cp -i "$work/source.txt" "$work/backup.txt"
```

Copy into a directory:

```bash
mkdir "$work/backup"
cp -i "$work/source.txt" "$work/backup/"
```

Copy a directory tree recursively:

```bash
cp -r "$work/backup" "$work/backup-copy"
```

Prompt before overwriting:

```bash
cp -i "$work/source.txt" "$work/copy.txt"
```

## Watch Out

`cp` can overwrite existing files. Use `cp -i` when practicing. Use `cp -r` only when you intend to copy a directory tree.

## Docs Pointers

- Run `man cp`.
- Read [file](../concepts/file.md), [directory](../concepts/directory.md), and [path](../concepts/path.md).
