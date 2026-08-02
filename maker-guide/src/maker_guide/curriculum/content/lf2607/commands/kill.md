# kill

## Use

```bash
kill 12345
kill -TERM 12345
kill -KILL 12345
```

## What It Does

`kill` sends a signal to a process id. The default signal is `TERM`, which asks a process to stop cleanly.

## Practice

Use `ps` first so you know the exact process id and owner.

```bash
ps -u "$USER" -o pid,comm,args
kill -TERM 12345
```

## Watch Out

Never guess process ids. `KILL` is a last resort because the process cannot clean up.

## Docs Pointers

- Run `man kill`.
- Read [signals](../concepts/signal.md), [processes](../concepts/process.md), [process basics](../concepts/process-basics.md), and [killall](killall.md).
