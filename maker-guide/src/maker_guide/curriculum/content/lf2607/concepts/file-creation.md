# File Creation

## Core Idea

Creating a file means creating a directory entry and, usually, initial file content.

The important question is not only "did a path appear?" It is also "what content and metadata did I create?"

## Tools

- `touch`: create an empty file or update its timestamp.
- `micro`: create or edit text interactively.
- `>`: create or replace a file with command output.
- `>>`: create or append to a file with command output.

## Proof Checks

```bash
work=$(mktemp -d)
touch "$work/empty.txt"
ls -l "$work/empty.txt"
printf 'hello\n' > "$work/hello.txt"
cat "$work/hello.txt"
```

Use `ls -l` to prove the path exists. Use `cat`, `less`, or `bat` to prove content.

## Watch Out

`touch` does not empty an existing file; `>` does. Inspect both size and content when checking what an operation changed.

## Docs Pointers

- Read [file](file.md), [directory](directory.md), [path](path.md), [I/O](io.md), and [redirection](stream-redirection.md).
- Read [touch](../commands/touch.md), [micro](../commands/micro.md), [redirect](../commands/redirect.md), and [append redirection](../commands/append-redirection.md).
