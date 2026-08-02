# File Descriptor

## Core Idea

A file descriptor is a small integer handle a process uses for an open file, pipe, socket, terminal, or device.

## Standard File Descriptors

| Number | Name | Usual Meaning |
|---|---|---|
| `0` | stdin | Input. |
| `1` | stdout | Normal output. |
| `2` | stderr | Error output. |

## Redirection Examples

```bash
ls /etc/hostname >out.txt
ls /no/such/path 2>error.txt
ls /etc/hostname /no/such/path >combined.txt 2>&1
ls /no/such/path 2>/dev/null
```

`>` is shorthand for redirecting file descriptor `1`. `2>` redirects file descriptor `2`. `2>&1` makes stderr point where stdout points at that moment.

## Why Order Matters

```bash
ls /etc/hostname /no/such/path >combined.txt 2>&1
```

This sends stdout to `combined.txt`, then sends stderr to the same destination.

```bash
ls /etc/hostname /no/such/path 2>&1 >out.txt
```

This first sends stderr to the old stdout, then sends stdout to `out.txt`. The result is different.

## Inspecting Open Descriptors

For your current shell process:

```bash
ls -l /proc/$$/fd
```

`$$` is the shell process id.

## Common Confusions

- File descriptors are per process.
- A descriptor can refer to something that is not a regular file, such as a pipe or socket.
- `2>&1` duplicates a destination; it does not mean "put descriptor 2 inside descriptor 1".
- Redirecting stderr to `/dev/null` hides errors. Do it only when you understand them.

## Proof Check

Run a command that produces both normal output and an error, redirect stdout and stderr separately, then inspect both files.

## Docs Pointers

- Run `man bash`, then search for `REDIRECTION`.
- Run `man proc` and inspect `/proc/self/fd`.
- Read [I/O](io.md), [Stream Redirection](stream-redirection.md), [Devices And `/dev`](devices.md), and [Sockets](sockets.md).
