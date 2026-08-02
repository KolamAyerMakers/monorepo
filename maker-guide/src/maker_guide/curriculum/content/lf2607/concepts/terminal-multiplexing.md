# Terminal Multiplexing

## Core Idea

Tmux runs terminal sessions on the server. An editor, build, download, server, or log watcher inside tmux can keep running when SSH disconnects.

Tmux survives a connection loss, not a server reboot or a broken command.

## Practice Alone

Create `workbench`, detach with `Ctrl-b d`, list sessions, and attach again:

```bash
tmux new -s workbench
tmux ls
tmux attach -t workbench
# detach again with Ctrl-b then d
tmux kill-session -t workbench
```

Detach again before `tmux kill-session`. Running `exit` in the final shell is another way to end the session.

## Done When

You can decide whether to detach and preserve work or exit and end the session.

## Go Deeper

- Read the [tmux command card](../commands/tmux.md) for windows, panes, movement, and recovery.
