# File

## Core Idea

A file is a named filesystem object that usually stores bytes plus metadata such as owner, permissions, size, and timestamps.

## Commands To Try

```bash
ls -l ~/src/pages/index.md
stat ~/src/pages/index.md
file ~/src/pages/index.md
cat ~/src/pages/index.md
```

`ls -l` shows compact metadata. `stat` shows detailed metadata. `file` guesses content type. `cat` prints file bytes as text.

## Content Versus Metadata

File content is the bytes inside the file. Metadata is information about the file: name, owner, group, mode, size, timestamps, and type. Editing a file changes content. `chmod` changes permission metadata.

## Source Versus Generated File

In this course:

- Source file: `~/src/pages/index.md`.
- Generated file: `~/public_html/index.html`.

Edit source. Rebuild generated files.

## Common Confusions

- File extension is a convention, not proof. Use `file` when content matters.
- A filename and the bytes it points to are related but not identical concepts.
- Deleting a file path removes a directory entry; recovery depends on backups or source regeneration.
- `cat` is for text. Use `file`, `strings`, or `xxd` for unknown data.

## Proof Check

Run `stat` on one source file and identify size, owner, permissions, and modification time.

## Docs Pointers

- Run `man stat`, `man file`, and `man chmod`.
- Read [Filesystem](filesystem.md), [File Encoding](file-encoding.md), and [Permissions](permissions.md).
