# Command: `rm`

## Use

```bash
work=$(mktemp -d)
printf 'disposable\n' > "$work/old.txt"
rm -i "$work/old.txt"
ls -la "$work"
```

## What It Does

`rm` removes directory entries. For ordinary files, that means the filename disappears from the directory.

## Safe Forms

Prompt before removing:

```bash
rm -i PATH
```

`rm -rf` means recursive and force. It can remove a whole directory tree without prompting, so understand it before you need it.

In the example, answer `y` only after reading the exact temporary path. `old.txt` should disappear. `PATH` above is a placeholder, not a file to create or a command to run unchanged. There is no automatic trash or undo.

## Watch Out

- Removal is real. Check the path before pressing Enter.
- Do not use `rm -rf` with variables until you can print the expanded path first.
- Use [rmdir](rmdir.md) for empty directories when you want a safer failure mode.

## Docs Pointers

- Run `man rm`.
- Read [file](../concepts/file.md), [directory](../concepts/directory.md), [path](../concepts/path.md), and [permissions](../concepts/permissions.md).
