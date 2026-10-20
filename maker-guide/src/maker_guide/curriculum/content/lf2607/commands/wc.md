# wc

## Use

```bash
printf 'one\ntwo\nthree\n' | wc -l
```

## What It Does

`wc` counts text. With `-l`, it counts newline characters; this example prints `3`.

## Practice

Pipe output into `wc -l` when you want a count instead of a screenful of text.

## Watch Out

`wc -l` counts newlines, not objects. A final line without a newline is not counted. Do not parse `ls` output to count files: names themselves can contain newlines.
