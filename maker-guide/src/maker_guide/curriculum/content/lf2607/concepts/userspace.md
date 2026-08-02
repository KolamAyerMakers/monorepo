# User Space

## Core Idea

User space is where normal programs run: shells, editors, git, curl, Python, Caddy, and your own scripts.

## Why It Exists

User-space programs have less privilege than the kernel. They ask the kernel to open files, create processes, allocate memory, and use the network. The kernel enforces permissions and isolation.

## Course Examples

```bash
ps -u "$USER" -o pid,comm,args | head
which bash
which curl
systemctl --user status site.service
```

Your systemd user service is a user-space process managed by your user account. It is not a root-managed system service.

## User Space Boundaries

- Your files live under your home directory unless explicitly shared.
- Your processes run as your user unless started by another account.
- Your services use `systemctl --user` when managed by your user account.
- You do not install system packages or edit system service units without admin involvement.

## Common Confusions

- User space does not mean graphical desktop. Server commands are user-space programs too.
- A user-space program can still be a server process.
- A process can fail because user-space configuration is wrong even when the kernel is fine.
- `sudo` changes privilege. It is not the normal path for this course.

## Proof Check

Run `ps -u "$USER" -o pid,comm,args | head`. Name three user-space processes owned by you.

## Docs Pointers

- Run `man ps`.
- Read [Kernel](kernel.md), [Syscall](syscall.md), and [Server](server.md).
- Read [Arch Wiki: systemd/User](https://wiki.archlinux.org/title/Systemd/User) as reference, not as an instruction to change system policy.
