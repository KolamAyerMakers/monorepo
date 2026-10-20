# Command: `mv`

## Use

```bash
work=$(mktemp -d)
printf 'draft\n' > "$work/draft.md"
mv -i "$work/draft.md" "$work/final.md"
ls "$work"
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
mv -i "$work/final.md" "$work/renamed.md"
```

Move into another directory, keeping the name:

```bash
mkdir "$work/finished"
mv -i "$work/renamed.md" "$work/finished/"
```

## Watch Out

`mv` can overwrite a target. Use `mv -i` while learning if overwriting would be expensive.

## Docs Pointers

- Run `man mv`.
- Read [path](../concepts/path.md), [file](../concepts/file.md), and [directory](../concepts/directory.md).
