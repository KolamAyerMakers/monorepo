# Multi-User Filesystems

## Core Idea

Shared Linux servers rely on users, groups, ownership, and permissions.

## Practice Alone

Compare files you own with system files and read the permission columns.

```bash
work=$(mktemp -d)
touch "$work/mine.txt"
ls -l "$work/mine.txt" /etc/passwd
ls -ld "$HOME" "$work" /etc
```

Identify owner, group, and the three permission triplets. The fresh temporary directory is private to your account by default. Do not change system-file permissions to make them resemble your file.

## Done When

You can explain why your home directory is not everyone else's workspace.

## Go Deeper

- [Permissions](permissions.md) explains owner, group, other, and permission bits.
- [Filesystem](filesystem.md) explains metadata and special filesystem paths.
