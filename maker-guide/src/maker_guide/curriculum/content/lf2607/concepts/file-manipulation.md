# File Manipulation

## Core Idea

File manipulation means changing directory entries and file content deliberately: copy, move, rename, remove, and inspect before and after.

## Operations

- Copy with `cp`: create another path with the same content.
- Move or rename with `mv`: change the path that points to the content.
- Remove with `rm`: remove a directory entry.
- Remove empty directories with `rmdir`: safer than recursive removal.

## Safety Pattern

```bash
pwd
work=$(mktemp -d)
printf 'draft\n' > "$work/source.txt"
cp -i "$work/source.txt" "$work/backup.txt"
mv -i "$work/backup.txt" "$work/final.txt"
rm -i "$work/final.txt"
ls -la "$work"
```

The example uses a fresh temporary directory. Answer the removal prompt only after checking its path; the original `source.txt` should remain afterward.

## Watch Out

The path is the thing you are changing. Read the full path before pressing Enter, especially with `rm` or `mv`.

## Docs Pointers

- Read [file](file.md), [directory](directory.md), [path](path.md), and [permissions](permissions.md).
- Read [cp](../commands/cp.md), [mv](../commands/mv.md), [rm](../commands/rm.md), and [rmdir](../commands/rmdir.md).
