# Path

## Core Idea

A path is a text name that tells Linux how to find a file, directory, or special filesystem object.

## Path Forms

- Absolute path: starts at `/`, such as `/etc/os-release`.
- Relative path: starts from the current directory, such as `pages/index.md`.
- Home path: starts with `~`, such as `~/notes.md`; Bash expands it to an absolute path.
- Current directory: `.`.
- File in the current directory: starts with `./`, such as `./report.sh`.
- Parent directory: `..`.

## Commands To Try

```bash
pwd
ls .
ls ..
ls ~
ls /etc/os-release
```

From `~/scripts`, if your saved script is `report.sh`, these name the same file:

```bash
./report.sh
~/scripts/report.sh
```

A bare `report.sh` is different: Bash searches the directories in `$PATH`. It does not automatically search the current directory.

## How The Shell Helps

The shell expands `~` before the command runs. The command receives the expanded path. Tab completion asks the shell to complete a path from the filesystem.

## Common Confusions

- `~/notes.md` and `notes.md` name the same path only when your current directory is your home.
- Paths are case-sensitive on normal Linux filesystems.
- Quote paths containing spaces: `"$HOME/my notes.md"`. Quoting `"~/my notes.md"` prevents Bash from expanding the tilde.
- `./foo.sh` means `foo.sh` here. It is a path, not special script syntax.
- A URL path and a filesystem path can look similar but belong to different systems.

## Proof Check

Run `cd /etc` and `pwd`, then compare `ls os-release` with `ls /etc/os-release`. Why do both work there, but only the second works from your home directory?

## Docs Pointers

- Run `man pwd`, `man cd`, and `man realpath`.
- Read [Filesystem](filesystem.md), [Directory](directory.md), and [File](file.md).
