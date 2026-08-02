# Filesystem

## Core Idea

A filesystem organizes persistent data into directories, files, metadata, and permissions.

## What You See As A User

```bash
pwd
ls -la
stat ~/src/pages/index.md
find ~ -maxdepth 2 -type f
```

Paths are names. Files have content. Directories contain names. Metadata includes owner, group, permissions, size, timestamps, and type.

## Important Path Ideas

- `/`: filesystem root.
- `~`: your home directory.
- `.`: current directory.
- `..`: parent directory.
- Absolute path: starts with `/`.
- Relative path: starts from the current directory.

## Filesystem Metadata

`ls -l` gives a compact view. `stat` gives a detailed view.

```bash
stat ~/src/pages/index.md
```

Look for file type, size, owner, group, permissions, and timestamps.

## Mounts And Virtual Filesystems

Some filesystem paths are not ordinary disk files. `/proc` exposes process and kernel information. `/dev/null` is a special device that discards bytes. These are still accessed through filesystem paths.

## Common Confusions

- A directory is not just a visual folder; it maps names to entries.
- Deleting a filename is not the same mental model as erasing every byte immediately.
- `~/src/pages/index.md` and `~/public_html/index.html` are different files with different roles.
- Editing generated output is fragile; edit source and rebuild.

## Proof Check

Run `stat ~/src/pages/index.md` and identify owner, permissions, size, and modification time.

## Docs Pointers

- Run `man hier`, `man stat`, `man find`, and `man 7 inode`.
- Read [Filesystem Navigation](filesystem-navigation.md) for beginner movement commands.
- Read [Path](path.md), [File](file.md), and [Directory](directory.md) for the objects you manipulate every session.
- Read [Permissions](permissions.md) and [Number Bases: Decimal, Hexadecimal, Octal](number-bases.md) for permission metadata.
- Read [Devices And `/dev`](devices.md) for special filesystem paths under `/dev`.
