# ps

## Use

```bash
ps -u "$USER" -o pid,comm,args
```

## What It Does

`ps` prints a snapshot of running processes.

## Practice

Use `-u "$USER"` to show processes owned by your account. The output columns are process id, command name, and arguments.

For a system-wide command-name stream:

```bash
ps -eo comm=
```

`-e` selects every process. `-o comm=` prints only the short command name and suppresses the heading.

## Watch Out

`ps` is a snapshot. It does not keep updating like `htop`.

Avoid `ps aux | grep "$USER"` as ownership proof. It searches text in the whole line and can match usernames, paths, or arguments that are not process owners.

## Docs Pointers

- Run `man ps`.
- Read [process basics](../concepts/process-basics.md), [processes](../concepts/process.md), and [signals](../concepts/signal.md).
