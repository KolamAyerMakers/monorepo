# Directory

## Core Idea

A directory is a filesystem object that maps names to entries such as files, subdirectories, and special objects.

## Commands To Try

```bash
pwd
ls -la
work=$(mktemp -d)
mkdir "$work/nested"
find "$work" -maxdepth 2 -type d
rmdir "$work/nested"
```

## Directory Permissions

Read permission lets you list names. Write **and execute** permissions let you add or remove entries. Execute permission lets you traverse the directory and access entries by name. Directory `x` matters even though a directory is not a program.

## Mental Model

Think of a directory as a table of names. The table itself has permissions and metadata. Entries inside it also have their own permissions and metadata.

## Common Confusions

- `rmdir` only removes empty directories.
- `rm -r` removes a directory tree and is dangerous outside scratch areas.
- A directory can be visible but not enterable if execute permission is missing.
- `.` and `..` are directory references, not ordinary project files.

## Proof Check

Run `ls -ld ~ /etc /usr` and compare directory permissions. Why does `-d` matter here?

## Docs Pointers

- Run `man mkdir`, `man rmdir`, `man find`, and `man chmod`.
- Read [Path](path.md), [Filesystem](filesystem.md), and [Permissions](permissions.md).
