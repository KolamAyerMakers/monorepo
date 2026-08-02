# Linux Foundations S3

Session: S3

Streams, pipes, processes

<!-- end_slide -->

# Today's Story

Unix tools become powerful when their input and output fit together.

Today you will route output, connect tools, and inspect what is running.

<!-- end_slide -->

# Three Standard Streams

When the shell starts a command, it normally connects three standard streams:

```text
stdin  (0) --> command --> stdout (1) --> normal results
                         \-> stderr (2) --> diagnostics, errors, warnings
```

By default, stdin reads from your terminal and both output streams appear on your terminal.

They look mixed together until you redirect them.

<!-- end_slide -->

# Watch Both Output Streams

Hands-on now: run one command that produces a result and an error.

```bash
$ ls /etc/hostname /no/such/path
ls: cannot access '/no/such/path': No such file or directory
/etc/hostname
```

- `/etc/hostname` is printed on stdout.
- The missing-path message is printed on stderr.

The terminal displays both, but they are separate streams.

<!-- end_slide -->

# Redirection Has Grammar

Read redirection as `[stream][operator][destination]`.

```text
>file          stdout -> file, replace it
>/dev/null     stdout -> black hole
>>file         stdout -> file, append
>>/dev/null    stdout -> black hole
2>file         stderr -> file, replace it
2>/dev/null    stderr -> black hole
2>&1           stderr -> wherever stdout points now
```

For `>` and `>>`, no number means stdout. `2` means stderr. `>` replaces; `>>` appends.

`/dev/null` is Linux's black hole: bytes written there disappear.

<!-- end_slide -->

# Separate The Streams

Hands-on now: send each stream to its own file.

```bash
mkdir -p ~/playground
ls /etc/hostname /no/such/path >~/playground/stdout.txt 2>~/playground/stderr.txt
cat ~/playground/stdout.txt
cat ~/playground/stderr.txt
cat /etc/hostname >/dev/null
```

The `ls` command fails because one path is missing. The two files still preserve useful evidence.

If errors matter, save and read them before sending them to `/dev/null`.

<!-- end_slide -->

# Combine The Streams

Redirections are applied from left to right.

```bash
ls /etc/hostname /no/such/path >~/playground/combined.txt 2>&1
cat ~/playground/combined.txt
```

Read the first line as:

1. Send stdout to `combined.txt`.
2. Send stderr to wherever stdout points now.

Both streams reach the same file.

<!-- end_slide -->

# Search Lines With grep

`grep` prints lines that match a pattern. Start with literal text. The `-n` option adds matching line numbers.

```bash
grep ssh /etc/services
grep -n ssh /etc/services
```

Recursive directory search and symbolic links come later. Search one known file or stream first.

<!-- end_slide -->

# A Pipe Connects Tools

The shell's `|` connects stdout on the left to stdin on the right.

```text
command A --stdout--> | --stdin--> command B
          --stderr----------------> terminal
```

Hands-on now: build one stage at a time.

`cut -d: -f1` selects the first colon-separated field. `wc -l` counts lines.

```bash
cut -d: -f1 /etc/passwd
cut -d: -f1 /etc/passwd | wc -l
```

The pipe carries `cut`'s stdout into `wc`'s stdin. If the result surprises you, remove the rightmost stage and inspect the previous output.

Explain in your own words which command writes to the pipe and which command reads from it.

<!-- end_slide -->

# Pipe Errors Deliberately

A normal pipe carries stdout, not stderr.

Use `2>&1` before the pipe when the error text is the data you want to process:

```bash
$ cat /etc/hostname /no/such/path 2>&1 | grep path
cat: /no/such/path: No such file or directory
```

Now `grep` can read the missing-path error because stderr joined stdout before the pipe.

<!-- end_slide -->

# Keep A Copy With tee

`tee` is a T-junction: it copies stdin to a file and also sends it onward through stdout.

```bash
cut -d: -f7 /etc/passwd | tee ~/playground/login-shells.txt | wc -l
cat ~/playground/login-shells.txt
```

One stream was transformed and saved while `wc` printed its count.

<!-- end_slide -->

# Put The Plumbing Together

Hands-on now: combine both output streams, save them, and count them.

```bash
date --debug +%F 2>&1 | tee ~/playground/combined.txt | wc -l
cat ~/playground/combined.txt
```

- GNU `date` prints an ISO date on stdout and an output-format diagnostic on stderr.
- The command succeeds: stderr can carry a diagnostic even when a command exits zero.
- `2>&1` combines the streams before the pipe.
- `tee` saves the combined output while `wc` counts its two lines.

Explain in your own words what descriptor 2 names and why left-to-right redirection sends the diagnostic through the pipe.

<!-- end_slide -->

# Demo: Ask A Real Question

Which login shell is configured for the most accounts on this server?

- `cut` selects field 7 from colon-separated lines.
- `sort` puts equal lines together.
- `uniq -c` counts each group.
- `sort -nr` ranks the counts from largest to smallest.

Now build and run the pipeline:

```bash
cut -d: -f7 /etc/passwd
cut -d: -f7 /etc/passwd | sort | uniq -c | sort -nr
```

This is the Unix workshop: each tool does one small job.

<!-- end_slide -->

# Program File To Process

Many external commands name executable program files, such as `/usr/bin/grep`.

A binary executable stores machine instructions and loading information as bytes. The kernel loads it into memory, and the CPU executes those instructions.

```text
/usr/bin/grep on disk -> kernel loads code -> process in memory -> CPU runs instructions
```

The program file remains on disk even when no process is running. When the shell asks the kernel to run it, Linux creates a process with its own process ID (PID), owner, memory, and open streams.

Not every command launches a separate executable. Shell built-ins such as `cd` and `history` run inside the shell.

<!-- end_slide -->

# Inspect Your Processes

Hands-on now: inspect only processes owned by your account.

`$USER` is a value the shell replaces with your username.

```bash
ps -u "$USER" -o pid,comm,args
```

- `PID`: unique process ID.
- First `COMMAND` column: short program name.
- Second `COMMAND` column: command and arguments, possibly clipped to terminal width.

Find your shell, your SSH connection, and any command you recognize. Pick one row and note its exact PID and command.

Explain in your own words how a program file differs from a running process, then identify the PID and command from your chosen row.

<!-- end_slide -->

# Demo: What Runs Most?

Use a pipeline to summarize the shared server's process table:

For this demo, `-e` selects every process and `-o comm=` prints only its short command name without a heading.

```bash
ps -eo comm= | sort | uniq -c | sort -nr | head
```

`ps` emits command names. The remaining stages group, count, rank, and trim them.

Predict the most common process before running it.

<!-- end_slide -->

# Exit Goal

Before leaving, you can:

- name stdin, stdout, and stderr;
- read common redirection syntax left to right;
- build and debug a pipeline;
- explain executable file versus running process;
- inspect processes owned by your account.

<!-- end_slide -->

# Between-Session Practice

See you on Saturday, 8 August to learn about permissions and Git.

There is no class on Saturday, 15 August. Our next class is Saturday, 22 August, when we start scripting.

Use `guide now` for the current objective. After objectives, it shows the current quest. Submit requested explanations with `guide answer 'your answer'` and run `guide check` after practical work.

1. Search one file with `grep`, then connect `cut` and `wc` with a pipe.
2. Separate stdout and stderr into files.
3. Combine stderr with stdout using `2>&1`.
4. Save a pipeline copy with `tee`.
5. Inspect your process table.
