# Command: `rm`

## Use

```bash
rm ~/playground/old.txt
rm -i ~/playground/old.txt
```

## What It Does

`rm` removes directory entries. For ordinary files, that means the filename disappears from the directory.

## Safe Forms

Prompt before removing:

```bash
rm -i file.txt
```

`rm -rf` means recursive and force. It can remove a whole directory tree without prompting, so understand it but do not run it in S2.

## Watch Out

- Removal is real. Check the path before pressing Enter.
- Do not use `rm -rf` with variables until you can print the expanded path first.
- Use [rmdir](rmdir.md) for empty directories when you want a safer failure mode.

## Docs Pointers

- Run `man rm`.
- Read [file](../concepts/file.md), [directory](../concepts/directory.md), [path](../concepts/path.md), and [permissions](../concepts/permissions.md).
