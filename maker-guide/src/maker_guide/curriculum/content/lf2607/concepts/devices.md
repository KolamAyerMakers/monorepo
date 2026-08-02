# Devices And `/dev`

## Core Idea

Linux exposes many devices through filesystem paths under `/dev`.

A device path is not an ordinary text file, even though commands can often open it like a file. It is an interface to the kernel or to hardware-like behavior.

## Useful Examples

```bash
ls -l /dev/null /dev/zero /dev/random /dev/tty
printf 'discard me\n' > /dev/null
```

- [`/dev/null`](dev-null.md): accepts writes and discards them; reads return end of file.
- `/dev/zero`: produces zero bytes when read.
- `/dev/random` and `/dev/urandom`: produce random bytes.
- `/dev/tty`: the controlling terminal for the current process when one exists.

## Why `/dev/null` Appears Early

```bash
find /etc -name '*.conf' 2>/dev/null
```

`2>` redirects stderr. `/dev/null` is the destination. This hides error output, so use it only after you understand what you are discarding.

## Device File Listing

```text
crw-rw-rw- 1 root root 1, 3 Aug 1 10:00 /dev/null
```

The leading `c` means character device. A leading `b` means block device. The numbers are device identifiers, not file size.

## Common Confusions

- `/dev/null` does not delete files; it discards bytes written to that special path.
- Device paths can have permissions just like other filesystem entries.
- Not every path that looks like a file stores bytes on disk.
- Do not write random data to unknown `/dev/*` paths.

## Proof Check

Run `ls -l /dev/null`, redirect a harmless message into it, then explain why no output appears.

## Docs Pointers

- Run `man null`, `man zero`, and `man tty`.
- Run `man 7 device`.
- Read [I/O](io.md), [file descriptors](file-descriptor.md), [stream redirection](stream-redirection.md), and [filesystem](filesystem.md).
