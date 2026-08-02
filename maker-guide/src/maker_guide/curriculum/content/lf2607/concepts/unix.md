# Unix

## Core Idea

Unix is the operating-system tradition behind Linux: files, processes, users, permissions, pipes, small tools, and text interfaces.

## The Useful Unix Ideas

- Everything important has a name in the filesystem or process table.
- Programs read text, write text, and return success or failure.
- Small tools become powerful when connected with pipes.
- Users and groups control ownership and permissions.
- Manual pages are part of the system, not external homework.

## Course Examples

```bash
whoami
pwd
ls -la
cat /etc/os-release
cut -d: -f1 /etc/passwd | wc -l
ps -u "$USER" -o pid,comm,args
```

These commands show Unix ideas directly: identity, current directory, file metadata, readable system files, pipelines, and processes.

## Common Confusions

- Unix is not one single current operating system in this course. It is a design lineage and vocabulary.
- Linux is Unix-like, not historically identical to original Unix.
- "Everything is a file" is a useful simplification, not a literal rule for every kernel object.
- Text streams are powerful, but structured data sometimes needs structured tools.

## Proof Check

Pick one command from the course and explain which Unix idea it demonstrates: file, process, user, permission, text stream, or manual page.

## Docs Pointers

- Run `man intro`.
- Run `man hier` to inspect filesystem layout documentation.
- Read [The Art of Unix Programming: Basics of the Unix Philosophy](http://www.catb.org/esr/writings/taoup/html/ch01s06.html) critically, as history and design culture.
- Read [Linux](linux.md) for the Linux-specific version of these ideas.
