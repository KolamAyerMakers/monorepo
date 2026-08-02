# File Creation

## Core Idea

Creating a file means creating a directory entry and, usually, initial file content.

The important question is not only "did a path appear?" It is also "what content and metadata did I create?"

## Course Tools

- `touch`: create an empty file or update its timestamp.
- `micro`: create or edit text interactively.
- `>`: create or replace a file with command output.
- `>>`: create or append to a file with command output.

## Proof Checks

```bash
touch ~/playground/empty.txt
ls -l ~/playground/empty.txt
printf 'hello\n' > ~/playground/hello.txt
cat ~/playground/hello.txt
```

Use `ls -l` to prove the path exists. Use `cat`, `less`, or `bat` to prove content.

## Watch Out

Empty files can be useful as markers, but most course proof needs content.

## Docs Pointers

- Read [file](file.md), [directory](directory.md), [path](path.md), [I/O](io.md), and [redirection](stream-redirection.md).
- Read [touch](../commands/touch.md), [micro](../commands/micro.md), [redirect](../commands/redirect.md), and [append redirection](../commands/append-redirection.md).
