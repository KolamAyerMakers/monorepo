# killall

## Use

```bash
ps -u "$USER" -o pid,comm,args
killall -TERM exact-process-name
```

## What It Does

`killall` sends a signal to processes by name.

## Practice

Prefer `kill` with a process id while learning. Use `killall` only when the process name is exact, unambiguous, and you have checked what matches.

```bash
ps -u "$USER" -o pid,comm,args
killall -TERM exact-process-name
```

## Watch Out

Process names can match more than you intended. Do not run broad commands like `killall python3` on the shared server; several unrelated tools can use Python.

## Docs Pointers

- Run `man killall`.
- Read [signals](../concepts/signal.md), [processes](../concepts/process.md), and [kill](kill.md).
