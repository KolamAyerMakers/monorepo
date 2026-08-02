# Pipes

## Core Idea

A pipe connects stdout from one process to stdin of another process.

The pipe character `|` is shell syntax, not a command. Bash creates the pipe, starts both commands, and connects their file descriptors. A normal pipe carries stdout, not stderr.

## First Pipeline

```bash
cut -d: -f1 /etc/passwd | wc -l
```

Read it left to right:

- `cut -d: -f1 /etc/passwd` prints account names to stdout.
- `|` connects that stdout to the next command's stdin.
- `wc -l` reads stdin and prints the line count.

## Build Pipelines Slowly

```bash
cut -d: -f1 /etc/passwd
cut -d: -f1 /etc/passwd | wc -l
```

Add one stage only after the previous stage makes sense.

## What Crosses The Pipe

Bytes cross the pipe. Usually those bytes are text lines, but the shell does not care. Tools such as `grep`, `sort`, `uniq`, `cut`, and `wc` cooperate because they can read stdin and write stdout.

## Common Patterns

Count matches:

```bash
cut -d: -f1 /etc/passwd | wc -l
```

Process errors as data:

```bash
cat /etc/hostname /no/such/path 2>&1 | grep path
```

Keep a copy while continuing the pipeline:

```bash
cut -d: -f7 /etc/passwd | tee ~/playground/login-shells.txt | wc -l
```

Count and rank login shells:

```bash
cut -d: -f7 /etc/passwd | sort | uniq -c | sort -nr
```

## Watch Out

- A pipeline can hide which stage failed. Test stages separately.
- Some commands wait for stdin. Press `Ctrl-C` if a pipeline hangs.
- Do not use `cat file | command` when `command file` works, unless you are teaching stdin deliberately.

## Proof Check

Run a three-stage pipeline and explain exactly what each stage reads and writes.

## Docs Pointers

- Run `man bash` and search for `Pipelines`.
- Read [I/O](io.md), [file descriptors](file-descriptor.md), [stream redirection](stream-redirection.md), [one-liners](oneliner.md), [regular expressions](regular-expression.md), [tee](../commands/tee.md), [sort](../commands/sort.md), and [uniq](../commands/uniq.md).
