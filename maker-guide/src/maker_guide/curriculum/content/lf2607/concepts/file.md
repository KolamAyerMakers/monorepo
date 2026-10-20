# File

## Core Idea

A file is a named filesystem object that usually stores bytes plus metadata such as owner, permissions, size, and timestamps.

## Commands To Try

```bash
ls -l /etc/os-release
stat /etc/os-release
file /etc/os-release
cat /etc/os-release
```

`ls -l` shows compact metadata. `stat` shows detailed metadata. `file` guesses content type. `cat` prints file bytes as text.

## Content Versus Metadata

File content is the bytes inside the file. Metadata is information about the file: name, owner, group, mode, size, timestamps, and type. Editing a file changes content. `chmod` changes permission metadata.

## Source Versus Generated File

For a generated website, for example:

- Source file: Markdown you edit, such as `pages/index.md`.
- Generated file: HTML produced by a build, such as `output/index.html`.

Edit source. Rebuild generated files.

## Common Confusions

- File extension is a convention, not proof. Use `file` when content matters.
- A filename and the bytes it points to are related but not identical concepts.
- Deleting a file path removes a directory entry; recovery depends on backups or source regeneration.
- `cat` is for text. Use `file`, `strings`, or `xxd` for unknown data.

## Proof Check

Run `stat /etc/passwd` and identify size, owner, permissions, and modification time. Do not edit the system file.

## Docs Pointers

- Run `man stat`, `man file`, and `man chmod`.
- Read [Filesystem](filesystem.md), [File Encoding](file-encoding.md), and [Permissions](permissions.md).
