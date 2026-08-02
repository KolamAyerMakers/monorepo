# diff

## Use

```bash
diff -u old.txt new.txt
```

## What It Does

`diff` shows differences between two files or streams.

## Use Unified Diff By Default

```bash
diff -u before.md after.md
```

Unified diff is the standard format used in patches and code review. It shows nearby context, removed lines with `-`, and added lines with `+`.

## Course Example

Compare source versions or generated output when debugging:

```bash
diff -u ~/src/pages/index.md ~/playground/index-copy.md
```

Do not start with HTML unless the bug is specifically in generated HTML. Source files are usually easier to read.

## Watch Out

No output usually means the inputs match.

## Docs Pointers

- Run `man diff`.
- Read [git diff](git-diff.md), [file](../concepts/file.md), and [text transforms](../concepts/text-transforms.md).
