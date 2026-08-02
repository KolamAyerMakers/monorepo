# stderr Redirect (`2>`)

## Use

```bash
ls /no/such/path 2>~/playground/errors.txt
```

## What It Does

`2>` sends stderr to a file.

## Practice

Use it when permission errors are useful evidence but should not mix with normal output.

```bash
ls /etc/hostname /no/such/path >~/playground/stdout.txt 2>~/playground/stderr.txt
```

## Watch Out

`>` redirects stdout. `2>` redirects stderr.

## Optional Exploration

`2>>` is optional exploration for later: it preserves existing error evidence and appends new errors.

## Docs Pointers

- Read [stderr to stdout](stderr-to-stdout.md), [I/O](../concepts/io.md), [file descriptors](../concepts/file-descriptor.md), [stream redirection](../concepts/stream-redirection.md), and [dev null](../concepts/dev-null.md).
