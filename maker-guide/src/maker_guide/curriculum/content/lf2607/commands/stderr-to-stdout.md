# stderr To Stdout (`2>&1`)

## Use

```bash
ls /etc/hostname /no/such/path >combined.txt 2>&1
```

## What It Does

`2>&1` sends stderr to the same destination stdout uses at that moment.

## Order Matters

```bash
ls /etc/hostname /no/such/path >combined.log 2>&1
```

This sends stdout to `combined.log`, then sends stderr there too.

```bash
ls /etc/hostname /no/such/path 2>&1 >stdout.log
```

This sends stderr to the old stdout first, then redirects stdout. The result is different.

## Process Errors In A Pipeline

```bash
ls /etc/hostname /no/such/path 2>&1 | grep path
```

A normal pipe carries stdout. `2>&1` first moves stderr onto stdout so `grep` can read the error text.

## Docs Pointers

- Read [stderr redirection](stderr-redirect.md), [I/O](../concepts/io.md), [file descriptors](../concepts/file-descriptor.md), and [stream redirection](../concepts/stream-redirection.md).
