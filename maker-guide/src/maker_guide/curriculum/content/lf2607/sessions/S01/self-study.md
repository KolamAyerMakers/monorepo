# S1 Self-Study Guide: First Contact

Session: S1

## Study Path

1. Choose a username you can live with. It is your Unix username.
2. On Windows, open Windows Terminal from Start. On macOS, open Terminal from Applications > Utilities.
3. If your account does not exist, run `ssh new@lf2607.kolamayermakers.org`. If you do not have an SSH client, use the [browser registration page](https://lf2607.kolamayermakers.org/register/). The kiosk creates your account, prints your real SSH command, then disconnects.
4. Reconnect with `ssh username@lf2607.kolamayermakers.org`. If you do not have an SSH client, use [browser SSH](https://lf2607.kolamayermakers.org/ssh/).
5. Prove identity and machine state with `whoami`, `hostname`, `date`, and `uptime`.
6. Join `#lf2607` at [the classroom IRC page](https://lf2607.kolamayermakers.org/irc/). Use `#kolamayermakers` for general chat.
7. Learn the map: `/` is the filesystem root, `~` is your home, `.` is here, `..` is parent. Run `cd /docs` to visit your course-material playground. Read anything in it and follow what interests you.
8. Read files with `cat`, `bat`, `less`, `head`, and `tail` before editing anything.
9. Generate your starter page with `build-website` and inspect the static URL.

## Mental Model

The shell is a text conversation with the operating system. A command has a name, arguments, output, and an exit result. Your prompt is not decoration: it tells you that you are logged in, where you are, and that the shell is waiting.

If you want the deeper distinction: the terminal is the text interface, SSH is the secure connection, and the shell is the program interpreting commands on the server.

## IRC

IRC is the shared class chat. Use `#lf2607` for help that other learners can learn from, including between sessions. Use `#kolamayermakers` for general chat.

Do not paste passwords, private keys, access tokens, or private account setup links into IRC.

## Expected Output Shapes

```bash
whoami
```

Expected: your handle, one line.

```bash
pwd
```

Expected: an absolute path such as `/home/username`.

```bash
ls -la ~
```

Expected: permission columns, owner, group, size, date, and names. Ignore `.` and `..` when counting home entries.

## Troubleshooting

- `Permission denied`: check the username before the `@`, then retry slowly.
- You landed in onboarding again: you connected as `new`; reconnect with the username you chose.
- Host key prompt appears: read it. Type `yes` only when the host is `lf2607.kolamayermakers.org`.
- Stuck in `less` or `man`: press `q`.
- Command is running too long: press `Ctrl-C`.
- You are lost or have a question: ask in `#lf2607`, including the command and error but no secrets.

## Proof Checklist

- `whoami` prints your handle.
- `cat /etc/os-release` shows which Linux distribution this machine runs.
- You can count home entries from `ls -la ~` without counting `.` and `..`.
- You can explain `ls -S` from `man ls`.
- You have run `head -n 5 /etc/services` and `tail -n 5 /etc/services`.
- `~/public_html/index.html` exists after running `build-website`.

## Docs Pointers

- Read [Docs Navigation Guide](../../guides/docs-map.md) before asking where a file is.
- Run `man ssh`, then read the `SYNOPSIS` and authentication parts.
- Run `man ls`, then search for `-S` with `/ -S` or by scanning options.
- Run `tldr ssh`, `tldr ls`, and `tldr cat` for short reminders.
- Read [Platform Reference](../../guides/platform-reference.md) before using public URLs.
- Read [Linux](../../concepts/linux.md), [Unix](../../concepts/unix.md), [Server](../../concepts/server.md), and [Client](../../concepts/client.md) for the course vocabulary behind the first login.
- Read [Path](../../concepts/path.md), [File](../../concepts/file.md), [Directory](../../concepts/directory.md), and [I/O](../../concepts/io.md) for the basic objects behind every command.
- Read [Kernel](../../concepts/kernel.md), [User Space](../../concepts/userspace.md), [Syscall](../../concepts/syscall.md), [Filesystem](../../concepts/filesystem.md), [CPU](../../concepts/cpu.md), and [Memory](../../concepts/memory.md) only if you want the optional systems deep dive.
- Read [Terminal](../../concepts/terminal.md) and [Shell](../../concepts/shell.md) to understand what is local, what is remote, and what interprets commands.
- Read [Readline](../../concepts/readline.md) and drill the keystrokes until prompt editing stops feeling clumsy.
- Read [Time Zones](../../concepts/time-zones.md) if timestamps or logs disagree with your local clock.
