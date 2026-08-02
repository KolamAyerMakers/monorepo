# Stream Redirection

## Core Idea

Commands have stdin, stdout, and stderr. Redirection sends those streams somewhere else.

Read redirection as `[stream][operator][destination]`:

```text
>file          stdout to file, replacing it
>/dev/null     stdout to the black hole
>>file         stdout to file, appending
>>/dev/null    stdout to the black hole
2>file         stderr to file, replacing it
2>>file        stderr to file, appending
2>/dev/null    stderr to the black hole
2>&1           stderr to wherever stdout points now
```

For `>` and `>>`, no descriptor means stdout. Descriptor `2` means stderr. Redirections are applied from left to right.

`2>>` is optional exploration for later: it appends stderr to a file instead of replacing the file.

## Practice Alone

```bash
ls /etc/hostname /no/such/path >stdout.txt 2>stderr.txt
ls /etc/hostname /no/such/path >combined.txt 2>&1
```

Read the two output files from the first command, then confirm the second command put both streams into one file.

## Done When

You choose `>`, `>>`, `2>`, `2>&1`, and `/dev/null` deliberately.

## Go Deeper

- [I/O](io.md) explains stdin, stdout, and stderr.
- [File descriptors](file-descriptor.md) explains why stderr is descriptor `2`.
- [Devices](devices.md) and [`/dev/null`](dev-null.md) explain discarded output.
- [One-liners](oneliner.md) explains grouped commands with one redirection.
- [Shell](shell.md) explains how Bash sets up redirection before starting a command.
