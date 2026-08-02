# CPU

## Core Idea

The CPU is the hardware that executes program instructions.

The CPU executes instructions for running processes. The kernel schedules which process gets CPU time and for how long.

## Commands To Try

```bash
uptime
ps aux --sort=-%cpu | head
htop
```

`uptime` shows load average. `ps` can show processes using CPU. `htop` shows an interactive view.

## Load Average

Load average is a rough count of runnable or waiting work over time windows. It is not the same as percentage CPU, and it only makes sense relative to CPU count and workload.

## Processes And Scheduling

Many processes appear to run at once. The kernel scheduler gives them turns on CPU cores. A stuck or busy process may consume CPU time even if it prints nothing.

## Common Confusions

- High CPU is not always bad; it may mean work is being done.
- A process can be slow because of disk, network, or waiting, not only CPU.
- Load average is not a direct percentage.
- Killing a process because it uses CPU is a decision, not a reflex.

## Proof Check

Run `ps aux --sort=-%cpu | head` and identify the command using the most CPU at that moment.

## Docs Pointers

- Run `man uptime`, `man ps`, and `man top`.
- Read [process basics](process-basics.md), [processes](process.md), [kernel](kernel.md), and [memory](memory.md).
