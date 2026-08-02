# Syscall

## Core Idea

A syscall is a controlled request from a user-space program to the kernel.

## Why Syscalls Exist

Programs should not directly control disks, memory, devices, users, or network hardware. They ask the kernel. The kernel checks permissions, performs the operation, and returns a result.

## Course Examples

- `cat file` asks the kernel to open and read a file.
- `mkdir directory` asks the kernel to create a directory.
- `ssh` asks the kernel to open a network connection.
- `python3 -m http.server --bind 127.0.0.1` asks the kernel to listen on a TCP port.
- `kill PID` asks the kernel to send a signal to a process.

## How To Observe Syscalls

`strace` is allowed in this course for observing your own small commands. Use it as a microscope, not as a stunt.

```bash
strace -e openat,read,write cat /etc/hostname
```

On a shared server, trace commands you start yourself. Do not try to attach to other learners' processes.

On machines without `strace`, skip the command. The syscall concept still matters.

## Common Confusions

- A syscall is not the same as a shell command.
- A permission error often comes from the kernel denying a syscall.
- A Python script and a Bash command both eventually use syscalls for files and networking.
- A syscall returning an error is not automatically a bug; it may be correct permission enforcement.

## Proof Check

Run `cat /etc/hostname`, then explain which kernel service was needed: file open, file read, or network connection.

## Docs Pointers

- Run `man 2 open`, `man 2 read`, and `man 2 write`.
- Run `man strace`.
- Read [kernel](kernel.md) and [userspace](userspace.md).
