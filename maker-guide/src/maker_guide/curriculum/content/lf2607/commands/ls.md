# Command: `ls`

## Use

```bash
ls
ls -la ~
```

## What It Does

`ls` lists directory entries.

## Useful Options

- `-a`: include hidden dotfiles.
- `-l`: long listing with type, permissions, owner, group, size, time, and name.
- `-h`: human-readable sizes when used with `-l`.
- `-S`: sort by size.
- `-t`: sort by modification time.

## Long Listing

```bash
ls -l ~/src/pages
```

The first column shows file type and permissions. The owner and group columns matter on a shared server.

## Watch Out

`ls` output is for humans. Scripts should usually use explicit paths, `find`, or shell globs instead of parsing decorative `ls` output.

## Docs Pointers

- Run `man ls`.
- Read [ls -l](ls-l.md), [directory](../concepts/directory.md), [permissions](../concepts/permissions.md), and [path](../concepts/path.md).
