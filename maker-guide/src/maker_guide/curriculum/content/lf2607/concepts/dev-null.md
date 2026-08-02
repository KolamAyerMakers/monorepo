# `/dev/null`

## Core Idea

`/dev/null` is Linux's black hole: a special device path that discards anything written to it.

It is not a command. Commands use it as an I/O destination.

## Why It Exists

Sometimes you deliberately do not want one stream. `/dev/null` is the standard Unix sink for that unwanted output.

```bash
ls /etc/hostname /no/such/path 2>/dev/null
```

That command keeps the existing path on stdout and discards the missing-path error on stderr.

## Behavior

- Writing to `/dev/null` succeeds and discards bytes.
- Reading from `/dev/null` returns end of file immediately.
- It appears under `/dev` because it is a device, not an ordinary file.

## Watch Out

Do not hide errors until you understand them. Redirect to a file first when errors might be useful evidence.

## Proof Check

Run this and explain why nothing appears:

```bash
echo 'discard me' >/dev/null
```

## Docs Pointers

- Run `man null`.
- Read [devices](devices.md), [I/O](io.md), [file descriptors](file-descriptor.md), and [stream redirection](stream-redirection.md).
