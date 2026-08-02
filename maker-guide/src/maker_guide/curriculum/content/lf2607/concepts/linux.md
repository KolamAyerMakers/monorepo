# Linux

## Core Idea

Linux is the operating-system kernel at the center of a family of systems built from that kernel, system tools, libraries, services, shells, and applications.

## What You Are Using In This Course

You are using a shared Linux server. The exact distribution can be checked with:

```bash
cat /etc/os-release
uname -a
```

`/etc/os-release` identifies the distribution. `uname` reports kernel and machine information.

## Kernel, Distribution, Userland

- Kernel: manages processes, memory, filesystems, devices, and networking.
- Distribution: packages the kernel with tools, defaults, package repositories, and release policy.
- Userland: the commands and services you run, such as Bash, OpenSSH, Caddy, systemd, git, and curl.

## Why Linux Is Useful For Makers

- It exposes real systems as files, processes, sockets, logs, users, and permissions.
- It rewards small tools joined together.
- It runs servers, laptops, phones, routers, containers, and embedded systems.
- It is documented through manual pages and public source.

## Common Confusions

- Linux is not the same thing as Bash. Bash is one shell that runs on Linux.
- Linux is not the same thing as Ubuntu or Debian. Those are distributions.
- The desktop is optional. Servers often have no graphical interface.
- A command can be a Linux command, a GNU command, a Bash builtin, or a package-provided program.

## Proof Check

Run `cat /etc/os-release` and identify the distribution name. Run `uname -r` and identify the kernel release.

## Docs Pointers

- Run `man uname`.
- Read the [Debian Handbook](https://www.debian.org/doc/manuals/debian-handbook/).
- Read [kernel.org: What is Linux?](https://www.kernel.org/linux.html).
- Read [Unix](unix.md) to understand the older design tradition Linux grew from.
