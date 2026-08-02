# Path

## Core Idea

A path is a text name that tells Linux how to find a file, directory, or special filesystem object.

## Path Forms

- Absolute path: starts at `/`, such as `/etc/os-release`.
- Relative path: starts from the current directory, such as `pages/index.md`.
- Home path: starts with `~`, such as `~/src/pages/index.md`.
- Current directory: `.`.
- Parent directory: `..`.

## Commands To Try

```bash
pwd
ls .
ls ..
ls ~
ls /etc/os-release
```

## How The Shell Helps

The shell expands `~` before the command runs. The command receives the expanded path. Tab completion asks the shell to complete a path from the filesystem.

## Common Confusions

- `~/src/pages/index.md` and `src/pages/index.md` are not the same unless your current directory is your home.
- Paths are case-sensitive on normal Linux filesystems.
- Spaces in paths need quoting, but this course avoids spaces in filenames.
- A URL path and a filesystem path can look similar but belong to different systems.

## Proof Check

Run `pwd`, then explain whether `src/pages/index.md` would point at your site source from that location.

## Docs Pointers

- Run `man pwd`, `man cd`, and `man realpath`.
- Read [Filesystem](filesystem.md), [Directory](directory.md), and [File](file.md).
