# tmux

## Use

```bash
tmux new -s workbench
tmux ls
tmux attach -t workbench
# detach again with Ctrl-b then d
tmux kill-session -t workbench
```

## What It Does

`tmux` is a terminal multiplexer. It keeps terminal sessions alive after SSH disconnects and lets one SSH connection contain multiple windows or panes.

## First Session

Create a named session:

```bash
tmux new -s workbench
```

Detach without killing the session:

```text
Ctrl-b d
```

List sessions:

```bash
tmux ls
```

Attach again:

```bash
tmux attach -t workbench
```

After reattaching, detach again and end the named session:

```bash
tmux kill-session -t workbench
```

Running `exit` in the final shell also ends the session. Detach when work should continue; exit or kill the session when work is finished.

## Core Keys

Tmux uses a prefix key before most shortcuts. The default prefix is `Ctrl-b`.

| Action | Keys |
|---|---|
| Detach | `Ctrl-b d` |
| New window | `Ctrl-b c` |
| Next window | `Ctrl-b n` |
| Previous window | `Ctrl-b p` |
| Select window by number | `Ctrl-b <window number>` |
| Split horizontally | `Ctrl-b "` |
| Split vertically | `Ctrl-b %` |
| Move between panes | `Ctrl-b` then arrow key |
| Next pane layout | `Ctrl-b Space` |
| Zoom active pane | `Ctrl-b z` |

## Recovery

- `tmux ls` says no server: no tmux session exists, so create one.
- Nested tmux warning: you are already inside tmux. Detach or open a new window.
- Command still died: tmux preserves terminals, not broken commands.

## Docs Pointers

- Run `man tmux`.
- Read [tmux wiki](https://github.com/tmux/tmux/wiki).
- Read [terminal multiplexing](../concepts/terminal-multiplexing.md), [terminal](../concepts/terminal.md), and [SSH login](../concepts/ssh-login.md).
