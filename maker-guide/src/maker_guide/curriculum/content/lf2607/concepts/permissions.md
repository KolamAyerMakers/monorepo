# Permissions

## Core Idea

Unix permissions say who may read, write, and execute a path.

They are filesystem metadata. Changing permissions does not edit file content; it changes who can use that path and how.

## Long Listing Shape

```text
-rw-r--r-- 1 username username 12 Aug 1 10:00 hi.txt
| |  |  |
| |  |  other: read only
| |  group: read only
| owner: read and write
regular file
```

The first character is the file type. The next nine characters are three permission triplets: owner, group, other.

## Bits

| Bit | File Meaning | Directory Meaning |
|---|---|---|
| `r` | Read file content. | List directory names. |
| `w` | Write file content. | Add, remove, or rename entries. |
| `x` | Execute the file as a program or script. | Traverse through the directory. |

Directory execute permission is easy to miss. Without it, a user may know a directory exists but cannot enter it or reach paths below it.

## Symbolic Changes

```bash
chmod u+x script.sh
chmod go-r private-notes.txt
chmod a+r public-page.html
```

- `u`: owner.
- `g`: group.
- `o`: other.
- `a`: all three classes.
- `+`: add a bit.
- `-`: remove a bit.
- `=`: set exactly these bits.

## Octal Modes

Octal modes are the same permission bits written as numbers.

Each permission has a value:

| Bit | Value |
|---|---:|
| `r` | 4 |
| `w` | 2 |
| `x` | 1 |

Add the values in each triplet:

- `rwx` is `4 + 2 + 1 = 7`.
- `rw-` is `4 + 2 = 6`.
- `r--` is `4`.
- `---` is `0`.

The three digits are owner, group, and other:

| Mode | Text Form | Meaning |
|---|---|---|
| `644` | `rw-r--r--` | Owner can edit; everyone can read. Common for public files. |
| `755` | `rwxr-xr-x` | Owner can edit and execute; everyone can read and execute. Common for scripts and public directories. |
| `600` | `rw-------` | Only owner can read and write. Common for private files. |
| `700` | `rwx------` | Only owner can enter or execute. Common for private directories. |

Use symbolic modes when you are changing one bit deliberately, such as `chmod u+x script.sh`. Use octal modes when you want to set the full permission shape at once, such as `chmod 644 page.html` or `chmod 755 script.sh`.

Directories need `x` to be entered or traversed, so public web directories usually need `755`, not just read permission.

## Practice Alone

Use `ls -l` before and after `chmod` so the permission text becomes visible.

```bash
touch ~/playground/permission-test.txt
ls -l ~/playground/permission-test.txt
chmod go-r ~/playground/permission-test.txt
ls -l ~/playground/permission-test.txt
chmod u+x ~/playground/permission-test.txt
ls -l ~/playground/permission-test.txt
```

Do this only in scratch files you own.

## Common Failures

- `Permission denied`: read the path, owner, group, and bits with `ls -l` or `ls -ld`.
- Script still fails after `chmod +x`: executable permission only permits execution; it does not fix syntax or shebang problems.
- Directory is visible but unusable: check execute permission on every parent directory.
- Public file is still unreachable: check the file and the directories above it.

## Done When

You can read owner, group, and other permission triplets.

## Docs Pointers

- Run `man chmod`, `man ls`, and `man stat`.
- Read [Filesystem](filesystem.md), [File](file.md), [Directory](directory.md), and [Script Permissions](script-permissions.md).
- Read [Number Bases: Decimal, Hexadecimal, Octal](number-bases.md) before using numeric modes such as `644` or `755`.
