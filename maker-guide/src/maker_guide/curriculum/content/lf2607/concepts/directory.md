# Directory

## Core Idea

A directory is a filesystem object that maps names to entries such as files, subdirectories, and special objects.

## Commands To Try

```bash
pwd
ls -la
mkdir -p ~/playground/nested
rmdir ~/playground/nested
find ~/src -maxdepth 2 -type d
```

## Directory Permissions

Read permission lets you list names. Write permission lets you add or remove entries. Execute permission lets you traverse into the directory. Directory execute permission is why `x` matters even when a directory is not a program.

## Mental Model

Think of a directory as a table of names. The table itself has permissions and metadata. Entries inside it also have their own permissions and metadata.

## Common Confusions

- `rmdir` only removes empty directories.
- `rm -r` removes a directory tree and is dangerous outside scratch areas.
- A directory can be visible but not enterable if execute permission is missing.
- `.` and `..` are directory references, not ordinary project files.

## Proof Check

Run `ls -ld ~ ~/src ~/src/pages` and compare directory permissions.

## Docs Pointers

- Run `man mkdir`, `man rmdir`, `man find`, and `man chmod`.
- Read [Path](path.md), [Filesystem](filesystem.md), and [Permissions](permissions.md).
