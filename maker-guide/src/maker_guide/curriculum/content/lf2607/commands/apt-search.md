# apt search

## Use

```bash
apt search ascii
```

## What It Does

`apt search` finds packages by name or description.

It searches configured Debian package repositories. It does not search your files and it does not install anything.

## Practice

Use it for discovery on the shared server. Installation is an administrator action.

```bash
apt search terminal
apt search '^curl$'
```

Read package names and descriptions. Then use `apt show PACKAGE` for detail.

## Watch Out

Searching is safe. Installing with sudo is not part of this shared-server course.

## Docs Pointers

- Run `man apt`, then read `search`.
- Read [apt show](apt-show.md) and [package management](../concepts/package-management.md).
