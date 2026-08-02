# wc

## Use

```bash
ls ~/playground | wc -l
```

## What It Does

`wc` counts text. With `-l`, it counts lines.

## Practice

Pipe output into `wc -l` when you want a count instead of a screenful of text.

## Watch Out

`wc -l` counts lines, not objects. One line usually means one item only because `ls` printed one item per line.
