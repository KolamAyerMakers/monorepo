# Kernel

## Core Idea

The kernel is the privileged core of the operating system that manages processes, memory, filesystems, devices, and networking.

## What The Kernel Does For Your Commands

- Creates and stops processes.
- Reads program files from disk.
- Connects stdin, stdout, stderr, pipes, and redirection.
- Enforces file permissions.
- Schedules CPU time.
- Maps memory.
- Sends packets through the network stack.

## Commands To Try

```bash
uname -a
uname -r
cat /proc/version
```

`uname -r` prints the running kernel release. `/proc/version` exposes kernel build information through the proc filesystem.

## Kernel Space And User Space

Kernel code runs with high privilege. Normal commands run in user space and ask the kernel for services through syscalls. This separation is why a bug in `grep` should not be able to directly overwrite another user's memory or disk files.

## Common Confusions

- Linux is technically the kernel, but people often say Linux to mean the whole operating system stack.
- Bash, git, curl, Caddy, and Python are user-space programs.
- Root is a powerful user account, not the same thing as the kernel.
- A kernel module is not the same thing as a package installed with `apt`.

## Proof Check

Run `uname -r` and identify the kernel release. Then run `ps -p 1 -o comm=` and identify the first user-space process on this system.

## Docs Pointers

- Run `man uname` and `man proc`.
- Read [kernel.org: What is Linux?](https://www.kernel.org/linux.html).
- Read [User Space](userspace.md) and [Syscall](syscall.md) next.
