# Process

## Core Idea

A program can be an executable file stored on disk. A binary executable stores machine instructions and loading information as bytes. The kernel loads those instructions into memory so the CPU can execute them.

A process is one running instance of a program with its own process id, owner, memory, open files, environment, current directory, and execution state. Starting the same executable twice creates two processes.

## Commands To Try

```bash
ps -u "$USER" -o pid,comm,args
```

`pid` is the process id. `comm` is the command name. `args` shows the command line.

## Process Relationships

Processes form a tree. Your shell starts commands as child processes. A systemd user service is started and supervised by your per-user systemd instance. A web server process can create sockets, read files, and write logs.

## State To Notice

- Running or runnable: wants CPU time.
- Sleeping: waiting for input, time, disk, or network.
- Stopped: paused by job control or a signal.
- Zombie: exited, but parent has not collected its result yet.

## Signals

Signals are notifications sent to processes. `Ctrl-C` usually sends interrupt to the foreground process. `kill PID` sends a signal to a process id. A signal is not magic; the kernel delivers it and the process may handle or terminate from it depending on the signal.

## Common Confusions

- A program file is not a process. A process is one running instance of that program.
- Shell builtins such as `cd` and `history` run inside Bash instead of launching a process from a separate executable file.
- Closing a terminal may end child processes unless tmux, systemd, or another supervisor keeps them alive.
- A process can be alive but not listening on the port you expected.
- Killing by name with `killall` is broader than killing one known process id.

## Proof Check

Run `ps -u "$USER" -o pid,comm,args`. Pick one process and identify its pid, command name, and why it is running.

## Docs Pointers

- Run `man ps`, `man kill`, and `man signal`.
- Read [Process Basics](process-basics.md), [CPU](cpu.md), [Memory](memory.md), [Syscall](syscall.md), and [User Space](userspace.md).
