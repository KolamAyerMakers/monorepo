# I/O

## Core Idea

I/O means input and output: the bytes a process reads and writes through terminals, files, pipes, sockets, and devices.

## Standard Streams

When Bash starts a command, it normally connects three standard streams:

- stdin: input stream, file descriptor `0`.
- stdout: normal output stream, file descriptor `1`.
- stderr: error output stream, file descriptor `2`.

## Commands To Try

```bash
echo hello
cat < /etc/hostname
ls /etc /no/such/path > ~/playground/stdout.txt 2> ~/playground/stderr.txt
```

## Why It Matters

Pipes and redirection are I/O plumbing. They let small programs cooperate without knowing about each other. `grep` can read from a file or from stdin. `wc -l` can count file lines or pipeline lines.

## Common Confusions

- Output on the terminal can be stdout or stderr; they look similar until redirected.
- A command can succeed and still print warnings.
- A command can fail and still print useful partial output.
- Network sockets and device paths are I/O too, not only files and terminals.

## Proof Check

Redirect stdout and stderr to different files, then explain which message landed where.

## Docs Pointers

- Run `man bash`, then search for `REDIRECTION`.
- Read [File Descriptor](file-descriptor.md), [Stream Redirection](stream-redirection.md), [Pipes](pipes.md), [Devices And `/dev`](devices.md), and [Sockets](sockets.md).
