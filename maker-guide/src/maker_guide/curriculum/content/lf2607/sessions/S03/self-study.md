# S3 Self-Study Guide: Streams, Pipes, Processes

Session: S3

## Study Path

1. Identify stdin, stdout, and stderr.
2. Redirect stdout and stderr separately before combining or discarding them.
3. Run each pipeline stage alone, then connect the stages with `|`.
4. Use `tee` when a stream must continue and also be saved.
5. Distinguish an executable program file from a running process.
6. Inspect processes owned by your account.

## Standard Streams

When the shell starts a command, it normally connects three standard streams:

| Descriptor | Name | Usual role |
|---|---|---|
| `0` | stdin | Input available to the command. |
| `1` | stdout | Normal results from the command. |
| `2` | stderr | Diagnostics, including errors and warnings. |

Run one command that produces both output streams:

```bash
ls /etc/hostname /no/such/path
```

Both streams normally appear on the terminal, so redirection is how you prove which is which.

## Redirection Grammar

Read redirection as `[stream][operator][destination]`:

```text
>file          stdout to file, replacing it
>/dev/null     stdout to the black hole
>>file         stdout to file, appending
>>/dev/null    stdout to the black hole
2>file         stderr to file, replacing it
2>/dev/null    stderr to the black hole
2>&1           stderr to wherever stdout points now
```

For `>` and `>>`, an omitted descriptor means stdout. Descriptor `2` means stderr.

`/dev/null` is a special device path that discards every byte written to it. Do not discard an error until you know it is irrelevant.

Separate stdout and stderr:

```bash
mkdir -p ~/playground
ls /etc/hostname /no/such/path >~/playground/stdout.txt 2>~/playground/stderr.txt
cat ~/playground/stdout.txt
cat ~/playground/stderr.txt
cat /etc/hostname >/dev/null
```

Combine them by applying redirections from left to right:

```bash
ls /etc/hostname /no/such/path >~/playground/combined.txt 2>&1
cat ~/playground/combined.txt
```

First stdout points to `combined.txt`; then stderr points to stdout's current destination.

## Search With grep

`grep` prints lines that match a pattern. Start with literal text in one known file. The `-n` option adds matching line numbers:

```bash
grep ssh /etc/services
grep -n ssh /etc/services
```

Recursive directory search and symbolic links come later.

## Build Pipelines Slowly

A normal pipe connects stdout from the left command to stdin of the right command. It does not carry stderr.

`cut -d: -f1` selects the first colon-separated field. `wc -l` counts lines.

```bash
cut -d: -f1 /etc/passwd
cut -d: -f1 /etc/passwd | wc -l
```

If the final result surprises you, remove the rightmost stage and inspect the previous output.

Submit your own explanation with `guide answer 'your explanation'`.

When you need to process error text too, move stderr onto stdout before the pipe:

```bash
cat /etc/hostname /no/such/path 2>&1 | grep path
```

## Keep A Copy With tee

`tee` copies stdin to a file and also sends it onward through stdout.

```bash
cut -d: -f7 /etc/passwd | tee ~/playground/login-shells.txt | wc -l
cat ~/playground/login-shells.txt
```

The same stream is transformed, saved, and counted without a temporary pipeline stage.

Put both output streams through the same pipeline:

```bash
date --debug +%F 2>&1 | tee ~/playground/combined.txt | wc -l
cat ~/playground/combined.txt
```

GNU `date` writes an ISO date to stdout and an output-format diagnostic to stderr. It still exits zero: stderr can carry diagnostics even when a command succeeds. `2>&1` combines the streams before `tee` saves them and `wc` prints their line count, `2`.

Submit your own explanation of descriptor 2 and the left-to-right meaning of `2>&1` with `guide answer 'your explanation'`.

## A Useful Pipeline

Ask which login shell is configured for the most accounts:

`cut` selects field 7 from each colon-separated line. `sort` groups equal shells, `uniq -c` counts each group, and the final `sort -nr` ranks the counts from largest to smallest.

```bash
cut -d: -f7 /etc/passwd
cut -d: -f7 /etc/passwd | sort | uniq -c | sort -nr
```

## Program Files And Processes

Many external commands name binary executable files, such as `/usr/bin/grep`. A binary executable stores machine instructions and loading information as bytes. The kernel loads it into memory, then the CPU executes those instructions.

The executable is the program file on disk. When the shell asks the kernel to run it, Linux creates a process: a running instance with its own process ID, owner, memory, arguments, and open streams.

Shell built-ins, including `cd` and `history`, run inside the shell instead of launching a separate executable.

`$USER` is a shell-provided value containing your username. Environment variables get a full lesson in S5.

Inspect your own processes:

```bash
ps -u "$USER" -o pid,comm,args
```

The output has a PID, a short command name, and the command with arguments. Long arguments can be clipped to the terminal width. Pick one row and note its numeric PID and command.

Submit your own explanation of program file versus process, including the numeric PID and command from your chosen row, with `guide answer 'your explanation'`.

## Troubleshooting

- stdout and stderr still look mixed: redirect each to a different file, then read both files.
- `2>&1` went somewhere unexpected: read every redirection from left to right.
- `grep` prints nothing: no line matched. Run the left pipeline stage alone and inspect its exact output.
- `wc -l` looks wrong: it counts lines, not abstract objects.
- Pipeline hangs: the right command may be waiting for stdin. Press `Ctrl-C` and test each stage alone.

## Proof Checklist

- You can name stdin, stdout, and stderr and their descriptor numbers.
- `~/playground/stdout.txt` and `~/playground/stderr.txt` contain different streams.
- You can explain where stderr goes in `>combined.txt 2>&1`.
- You can explain every stage of one useful pipeline.
- `~/playground/login-shells.txt` contains the stream copied by `tee`.
- You can explain executable program file versus running process.
- You can name one process owned by your account.

## Docs Pointers

- Run `man bash`, then search for `REDIRECTION` and `Pipelines`.
- Run `man date`, `man grep`, `man tee`, and `man ps`.
- Read [I/O](../../concepts/io.md), [Pipes](../../concepts/pipes.md), [Stream Redirection](../../concepts/stream-redirection.md), [File Descriptor](../../concepts/file-descriptor.md), and [`/dev/null`](../../concepts/dev-null.md).
- Read [Process Basics](../../concepts/process-basics.md) and [Process](../../concepts/process.md).
- Use the [date](../../commands/date.md), [tee](../../commands/tee.md), [stderr redirect](../../commands/stderr-redirect.md), [stderr to stdout](../../commands/stderr-to-stdout.md), and [ps](../../commands/ps.md) command cards for exact syntax.
