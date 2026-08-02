# Memory

## Core Idea

Memory is hardware working storage that the CPU can access quickly.

Memory is fast working storage used by running processes and the kernel. Files persist on disk; memory usually disappears when a process exits or the machine restarts.

## Commands To Try

```bash
free -h
ps aux --sort=-%mem | head
htop
```

`free -h` shows memory totals in human-readable units. `ps` and `htop` show process memory usage.

## Virtual Memory

Processes see virtual memory, not direct physical RAM. The kernel maps virtual memory to RAM, files, shared libraries, and sometimes swap. This lets processes be isolated from each other.

## Common Fields

- RSS: resident memory currently in RAM for a process.
- VSZ or VIRT: virtual address space, often much larger than actual RAM use.
- Swap: disk-backed memory used when RAM pressure is high.
- Cache: memory Linux uses to speed up filesystem access and can reclaim when needed.

## Common Confusions

- Low free memory is not always bad; Linux uses memory for cache.
- Virtual memory size is not the same as physical memory use.
- A process can be killed if the system runs out of memory.
- Memory leaks are growth over time, not merely one large value.

## Proof Check

Run `free -h` and identify total memory, used memory, free memory, and available memory.

## Docs Pointers

- Run `man free`, `man ps`, and `man proc`.
- Read [process basics](process-basics.md), [processes](process.md), [kernel](kernel.md), [userspace](userspace.md), and [CPU](cpu.md).
