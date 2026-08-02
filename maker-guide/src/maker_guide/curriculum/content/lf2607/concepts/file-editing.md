# File Editing

## Core Idea

Editing changes file contents through a text editor.

The habit is simple:

1. Open the exact path.
2. Make the change.
3. Save.
4. Quit.
5. Verify with `cat` or another reader.

## Practice Alone

```bash
mkdir -p ~/playground
micro ~/playground/editing-note.txt
cat ~/playground/editing-note.txt
```

Make one small edit, save, quit, then verify from the shell. The shell verification matters because it proves the file changed on disk, not only inside the editor screen.

## Watch Out

- Open the exact path you intend to edit.
- Save before quitting.
- If the file is generated output under `~/public_html/`, fix the source under `~/src/` instead.

## Done When

You can edit a named file, save it, quit the editor, and prove the content with `cat`.

## Docs Pointers

- Read [micro](../commands/micro.md), [cat](../commands/cat.md), and [site source ownership](site-source-ownership.md).
