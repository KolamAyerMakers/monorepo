# kill

## Use

```bash
sleep 300 &
demo_pid=$!
ps -p "$demo_pid" -o pid,user,comm,args
kill -TERM "$demo_pid"
wait "$demo_pid"
```

## What It Does

`kill` sends a signal to a process id. The default signal is `TERM`, which asks a process to stop cleanly.

## Practice

The example starts a harmless `sleep`, captures its PID with `$!`, inspects it, and stops only that process. `wait` collects its result; a termination message and nonzero status are expected.

For any other process, inspect its exact PID and owner before acting. A PID printed earlier can be reused after that process exits.

## Watch Out

Never guess process IDs. `kill -KILL PID` is a last resort because the process cannot clean up. For a managed service, use its service manager so the restart policy does not immediately start it again.

## Docs Pointers

- Run `man kill`.
- Read [signals](../concepts/signal.md), [processes](../concepts/process.md), [process basics](../concepts/process-basics.md), and [killall](killall.md).
