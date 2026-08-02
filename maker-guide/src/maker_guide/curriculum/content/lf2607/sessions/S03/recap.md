# S3 Recap: Streams, Pipes, Processes

Session: S3

## Core Idea

The shell is an I/O workshop. Small programs cooperate by reading stdin, writing stdout and stderr, and connecting those streams to files, `/dev/null`, and other programs.

## Keep These Models

- stdin is descriptor `0`; stdout is `1`; stderr is `2`.
- stderr can carry a diagnostic even when a command succeeds; exit status reports success or failure.
- `>` replaces, `>>` appends, and a leading `2` selects stderr.
- `/dev/null` is a black hole for bytes you deliberately discard.
- `2>&1` points stderr at stdout's current destination.
- `|` connects stdout on the left to stdin on the right.
- `tee` copies stdin to a file and onward through stdout.
- An executable program file is stored on disk; a process is one running instance.

## Practice

```bash
mkdir -p ~/playground
ls /etc/hostname /no/such/path >~/playground/stdout.txt 2>~/playground/stderr.txt
cat /etc/hostname >/dev/null
date --debug +%F 2>&1 | tee ~/playground/combined.txt | wc -l
ps -u "$USER" -o pid,comm,args
```

## Recovery By Topic

- Streams: redirect stdout and stderr to separate files so you can see which produced each line.
- Pipes: remove the rightmost stage and inspect the previous output.
- Processes: inspect only your own process table and read the command before drawing conclusions.

## Live Core

You have the live milestone when you can read redirection left to right, explain one multi-stage pipeline, distinguish an executable from a process, and inspect a process you own.

## Can You Explain This?

- Why does a normal pipe carry stdout but not stderr?
- Where does stderr go in `>combined.txt 2>&1`?
- How does `tee` let one stream take two paths?
- What changes when an executable file becomes a process?
- Which PID and command can you identify in your own `ps` output?

## Optional Reinforcement

Run `guide now` for your current session objective. After the objectives, it shows the current S3 quest. Submit requested explanations with `guide answer 'your answer'` and run `guide check` after practical work.

## Full Autonomy

Use the [S3 self-study guide](self-study.md) for the full examples, troubleshooting, proof checklist, and reference-card links.
