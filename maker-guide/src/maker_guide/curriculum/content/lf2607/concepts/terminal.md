# Terminal

## Core Idea

A terminal is the text interface you use to talk to programs. In this course, your terminal usually runs an SSH client locally, and that SSH client connects you to a shell on `lf2607.kolamayermakers.org`.

## Terminal Versus Shell

The terminal is the window, tab, pane, or app that displays text and sends your keystrokes. The shell is the program interpreting commands after you log in. If the terminal closes, the display connection ends. If a shell process exits, the command session ends.

```text
keyboard -> terminal -> ssh -> remote shell -> Linux commands
```

Tmux sits inside this path and keeps a terminal session alive on the remote server even if your local SSH connection drops.

## What The Terminal Handles

- Drawing text output.
- Sending keystrokes such as Enter, Backspace, Tab, Ctrl-C, and Ctrl-D.
- Copy and paste.
- Scrollback history in the terminal app.
- Window, tab, or pane layout.

## What The Shell Handles

- Command parsing.
- Variable expansion such as `$HOME`.
- Redirection such as `>` and `2>`.
- Pipes such as `|`.
- Exit statuses.
- Running programs.

## Common Confusions

- Terminal scrollback is not the same as shell history.
- Closing a terminal is not the same as cleanly exiting a shell with `exit`.
- Copying a command can paste hidden spaces or line breaks; read before pressing Enter.
- Ctrl-C interrupts the foreground program; it does not close the terminal.
- Ctrl-D sends end-of-file to the shell; at an empty prompt, it usually logs out.

For prompt editing muscle memory, read [Readline](readline.md).

## Proof Check

Open two terminal tabs and SSH into the server from both. Run `tty` in each. Different terminal sessions should show different pseudo-terminal paths such as `/dev/pts/2`.

## Docs Pointers

- Run `man tty`.
- Run `man stty` only when you are curious about terminal modes.
- Read [The TTY demystified](https://www.linusakesson.net/programming/tty/) for a deep historical explanation.
- Read [Shell](shell.md) next to separate the terminal interface from the command interpreter.
- Read [Readline](readline.md) to practice prompt-editing keystrokes.
