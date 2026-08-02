# Command Form: `>>`

## Use

```bash
printf 'again\n' >> ~/playground/hi.txt
```

## What It Does

`>>` sends stdout to the end of a file. It creates the file if needed and preserves existing content.

## Practice

```bash
printf 'first\n' > ~/playground/hi.txt
printf 'second\n' >> ~/playground/hi.txt
cat ~/playground/hi.txt
```

Both lines remain because only the first command overwrites.

## Watch Out

Appending generated output repeatedly can create duplicates. If output should be idempotent, generate the full file from source instead of appending fragments forever.

## Docs Pointers

- Read [overwrite redirection](redirect.md), [I/O](../concepts/io.md), [file descriptors](../concepts/file-descriptor.md), and [stream redirection](../concepts/stream-redirection.md).
