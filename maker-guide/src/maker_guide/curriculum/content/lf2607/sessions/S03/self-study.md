# S3 — Streams, Pipes, Processes

Separate results from errors, connect commands, and identify a running process.

**You need:** a classroom shell or Ubuntu terminal. These examples work in either. Use `~/playground` for saved output.

## 1. See two output streams

Commands normally have three standard streams:

| Number | Name | Purpose |
|---|---|---|
| `0` | stdin | Input |
| `1` | stdout | Normal results |
| `2` | stderr | Diagnostics: errors, warnings, other messages |

```bash
ls /etc/hostname /no/such/path
```

The valid filename and the error both appear on your terminal. Separate them to see which stream carries each:

```bash
mkdir -p ~/playground
ls /etc/hostname /no/such/path >~/playground/stdout.txt 2>~/playground/stderr.txt
cat ~/playground/stdout.txt
cat ~/playground/stderr.txt
```

The first file contains `/etc/hostname`; the second contains the missing-path diagnostic. Their wording may vary.

## 2. Redirect deliberately

| Syntax | Effect |
|---|---|
| `>file` | Replace a file with stdout |
| `>>file` | Append stdout |
| `2>file` | Replace a file with stderr |
| `>/dev/null` | Discard stdout |
| `2>&1` | Send stderr wherever stdout points **at this step** |

Redirections apply **left to right**:

```bash
ls /etc/hostname /no/such/path >~/playground/combined.txt 2>&1
cat ~/playground/combined.txt
```

First stdout goes to the file; then stderr follows it. Reverse the redirections and stderr still goes to the terminal's original stdout.

`/dev/null` discards anything written to it. Try `cat /etc/hostname >/dev/null`: no output appears. Do not hide an error before understanding it.

## 3. Build a pipeline one stage at a time

A pipe, `|`, carries the left command's **stdout** into the right command's **stdin**. It does not carry stderr.

```bash
grep -n ssh /etc/services
cut -d: -f1 /etc/passwd
cut -d: -f1 /etc/passwd | wc -l
```

`grep` prints matching lines; `-n` adds line numbers. `cut` selects field 1 using `:` as the separator. `wc -l` counts newline characters—not users in every identity system.

Now ask: which login-shell value appears most often in local `/etc/passwd`?

```bash
cut -d: -f7 /etc/passwd | sort | uniq -c | sort -nr
```

Read from left to right: select field 7 → group equal lines → count each group → rank counts largest first. `uniq` counts adjacent equal lines, so the first sort matters.

If a result surprises you, remove the rightmost stage and inspect its input.

## 4. Save a stream without stopping it

`tee` copies stdin to a file **and** stdout:

```bash
cut -d: -f7 /etc/passwd | tee ~/playground/login-shells.txt | wc -l
cat ~/playground/login-shells.txt
```

Check that the saved file has the same number of lines as the printed count.

To send diagnostics through a pipe too:

```bash
date --debug +%F 2>&1 | tee ~/playground/combined.txt | wc -l
cat ~/playground/combined.txt
```

GNU `date` prints the date to stdout and a format diagnostic to stderr; `wc` counts the two lines. It succeeds: **stderr is not proof of failure**. `2>&1` combines the streams before `tee` saves them, replacing the earlier practice contents of `combined.txt`.

## 5. Program file or process?

An executable file, such as `/usr/bin/grep`, is stored on disk. A **process** is a running instance with a process ID (PID), owner, memory, and open streams. Several processes can run the same program.

Shell built-ins such as `cd` run inside the shell rather than starting a separate executable.

```bash
ps -u "$USER" -o pid,comm,args
```

`$USER` contains your username; quotes preserve it as one argument. Find a row owned by you and note its PID and command. Long arguments may be clipped to the terminal width.

## Check yourself

1. Why do the two files in Exercise 1 contain different text?
2. Where does stderr go in `>file 2>&1`? What changes in `2>&1 >file`?
3. Why sort before `uniq -c`?
4. What does `tee` let the next command receive?
5. Is a PID a property of the executable file or the running instance?

[Answers](../../guides/self-study-answers.md#s3-streams-pipes-and-processes). References: [Stream Redirection](../../concepts/stream-redirection.md), [Pipes](../../concepts/pipes.md), and [ps](../../commands/ps.md).

## If you get stuck

- `grep` prints nothing: inspect the input; no line may match.
- A pipeline waits forever: a command may be waiting for stdin. Press `Ctrl-C`, then test each stage alone.
- Streams still seem mixed: send them to separate files before combining them.
