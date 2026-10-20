# Command: `micro`

Edit a text file.

```bash
work=$(mktemp -d)
micro "$work/note.txt"
```

Save before quitting. After editing, use `cat` to prove what the file contains.

## Essential Keys

- Save: `Ctrl-S`
- Quit: `Ctrl-Q`
- Cut line: `Ctrl-K`
- Paste line: `Ctrl-U`
- Find text: `Ctrl-F`

## Safe Workflow

1. Run `pwd` if you are unsure where you are.
2. Open the exact path with `micro path/to/file`.
3. Save with `Ctrl-S`.
4. Quit with `Ctrl-Q`.
5. Prove the file with `cat path/to/file`.

## Common Failures

- File opens empty: you may have opened a new path. Quit, run `ls` on the parent directory, and reopen the intended file.
- Cannot save: check whether the directory exists and whether you own the file.
- Terminal looks strange after quitting: run `clear`.
- Edited a generated file: find its source and rebuild; changes to output may disappear at the next build.

## Docs Pointers

- Run `tldr micro`.
- Read [micro editor documentation](https://micro-editor.github.io/).
