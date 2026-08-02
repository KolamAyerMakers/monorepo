# Filesystem Navigation

## Core Idea

Filesystem navigation is the skill of knowing where your shell is and choosing paths deliberately.

The filesystem is a tree of directories and files. Your shell always has one current working directory.

## Core Commands

- `pwd`: print where you are.
- `ls`: list nearby entries.
- `cd`: change directory.
- `find`: search a tree by rules.

## Path Vocabulary

- `/`: root of the filesystem.
- `~`: your home directory.
- `.`: current directory.
- `..`: parent directory.
- Absolute path: starts with `/`.
- Relative path: starts from the current directory.

## Lost Pattern

```bash
pwd
ls -la
cd ~
```

Return home, then navigate again deliberately.

## Docs Pointers

- Read [path](path.md), [filesystem](filesystem.md), [file](file.md), [directory](directory.md), [permissions](permissions.md), and [number bases](number-bases.md).
- Read [pwd](../commands/pwd.md), [ls](../commands/ls.md), [cd](../commands/cd.md), and [find](../commands/find.md).
