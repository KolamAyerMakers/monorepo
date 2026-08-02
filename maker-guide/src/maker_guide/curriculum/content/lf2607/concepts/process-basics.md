# Process Basics

## Core Idea

Many external commands name executable program files. Linux loads an executable into memory to create a process: one running instance with an owner, process id, command line, and resource usage.

Shell builtins such as `cd` and `history` run inside Bash rather than starting another executable.

## Practice Alone

Use `ps -u "$USER" -o pid,comm,args` for a snapshot of processes owned by your account.

## Done When

You can distinguish an executable file from a process, then name one process you own and explain why it is running.

## Go Deeper

- [Process](process.md) is the fuller process model.
- [CPU](cpu.md) explains CPU time and load.
- [Memory](memory.md) explains process memory and system memory.
- [Signal](signal.md) explains `Ctrl-C`, `Ctrl-Z`, `kill`, `fg`, and `bg`.
- [Syscall](syscall.md) explains how processes ask the kernel for services.
- [Kernel](kernel.md) and [User Space](userspace.md) explain the privilege boundary.
