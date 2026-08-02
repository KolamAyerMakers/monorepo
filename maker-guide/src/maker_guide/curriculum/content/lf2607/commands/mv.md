# Command: `mv`

## Use

```bash
mv old-name.txt new-name.txt
mv ~/playground/draft.md ~/playground/final.md
```

## What It Does

`mv` moves a directory entry from one path to another path.

That same operation covers both renaming and moving:

- Rename: the parent directory stays the same, but the final name changes.
- Move: the parent directory changes.
- Move and rename: both change at once.

## Examples

Rename in the same directory:

```bash
mv draft.md final.md
```

Move into another directory, keeping the name:

```bash
mv final.md ~/src/pages/
```

## Watch Out

`mv` can overwrite a target. Use `mv -i` while learning if overwriting would be expensive.

## Docs Pointers

- Run `man mv`.
- Read [path](../concepts/path.md), [file](../concepts/file.md), and [directory](../concepts/directory.md).
