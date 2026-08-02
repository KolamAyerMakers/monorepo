# Job Control

## Core Idea

The shell can stop, background, foreground, and list jobs attached to that shell.

Job control belongs to one shell session. It is useful for short experiments, not for keeping important work alive after disconnection.

## Practice Alone

Use `Ctrl-Z`, `jobs`, `bg`, and `fg` on harmless commands.

```bash
sleep 60
```

Press `Ctrl-Z`, then run:

```bash
jobs
bg
jobs
fg
```

Press `Ctrl-C` to stop the foreground `sleep`.

## Watch Out

- `Ctrl-Z` stops a job; it does not end it.
- `bg` resumes a stopped job in the background.
- `fg` brings a job back to the foreground.
- Job control is not enough for work that must survive SSH disconnects.

## Done When

You know when job control is enough and when a durable session or service is needed.

## Docs Pointers

- Read [jobs](../commands/jobs.md), [bg](../commands/bg.md), [fg](../commands/fg.md), and [signals](signal.md).
