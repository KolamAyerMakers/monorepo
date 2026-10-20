# diff

## Use

```bash
work=$(mktemp -d)
printf 'red\nblue\n' > "$work/old.txt"
printf 'red\ngreen\n' > "$work/new.txt"
diff -u "$work/old.txt" "$work/new.txt"
```

## What It Does

`diff` shows differences between two files or streams.

## Use Unified Diff By Default

Unified diff is the standard format used in patches and code review. It shows nearby context, removed lines with `-`, and added lines with `+`.

The example removes `blue` and adds `green`. The `---` and `+++` lines identify the old and new files; they are not changes to the file contents.

## Watch Out

Exit status `0` means identical, `1` means different, and values above `1` mean an error. A difference is an expected result, not a broken command.

## Docs Pointers

- Run `man diff`.
- Read [git diff](git-diff.md), [file](../concepts/file.md), and [text transforms](../concepts/text-transforms.md).
