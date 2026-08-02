# Command Form: `ls -l`

## Use

```bash
ls -l ~/playground
```

## What It Does

`ls -l` shows a long listing with permissions, ownership, size, timestamp, and name.

## Reading The First Column

```text
-rw-r--r--
drwxr-xr-x
```

The first character is type: `-` for a regular file, `d` for directory. The next nine characters are owner, group, and other permissions.

## Watch Out

Use `ls -ld directory` when you want the directory's own metadata instead of its contents.

## Docs Pointers

- Run `man ls` and search for `-l`.
- Read [ls](ls.md), [permissions](../concepts/permissions.md), and [directory](../concepts/directory.md).
