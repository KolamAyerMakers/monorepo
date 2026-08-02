# Signal

## Core Idea

A signal is a notification sent to a process to interrupt it, stop it, continue it, terminate it, or report an event.

## Signals You Meet Early

| Signal | Common Trigger | Meaning |
|---|---|---|
| `SIGINT` | `Ctrl-C` | Interrupt the foreground process. |
| `SIGTSTP` | `Ctrl-Z` | Stop the foreground process. |
| `SIGCONT` | `fg` or `bg` | Continue a stopped process. |
| `SIGTERM` | `kill PID` default | Ask a process to terminate. |
| `SIGKILL` | `kill -9 PID` | Force termination; cannot be handled. Use rarely. |

## Commands To Try

```bash
sleep 60
# press Ctrl-C
```

```bash
sleep 60
# press Ctrl-Z
jobs
fg
```

## Kill Safely

```bash
ps -u "$USER" -o pid,comm,args
kill PID
```

Use `ps` first. Kill only processes you understand and own.

## Common Confusions

- `kill` sends a signal; it does not always immediately destroy a process.
- `Ctrl-C` affects the foreground process attached to your terminal.
- `Ctrl-Z` stops a process; it does not end it.
- `kill -9` skips cleanup. Do not make it your first move.
- systemd stopping a service usually sends a termination signal to the service process.

## Proof Check

Start `sleep 60`, stop it with `Ctrl-Z`, show it with `jobs`, continue it with `fg`, then interrupt it with `Ctrl-C`.

## Docs Pointers

- Run `man signal`, `man kill`, and `help jobs`.
- Read [Process](process.md), [Job Control](job-control.md), and [Service](service.md).
