# Keep a tmux workbench

Quest: keep-tmux-workbench

## Optional Mission

**tmux** keeps a terminal session running while you disconnect from its view. Practise creating, leaving, and returning to a session; it is not needed for your systemd service.

## Steps

1. Run `tmux new -s quest-workbench`.
2. Detach: press `Ctrl-b`, release both keys, then press `d`. The session keeps running.
3. Run `tmux ls`.
4. Reattach with `tmux attach -t quest-workbench`.
5. Detach again with `Ctrl-b d`.
6. Run `tmux kill-session -t quest-workbench`.
7. Run `guide check` when this quest is current.

## If Check Fails

- If `quest-workbench` already exists, attach and inspect it first. Do not kill a session containing work you want to keep.
- If `tmux ls` says no server is running, create `quest-workbench` again.
- If tmux warns about nesting, detach from the current session first.

## Related Reading

- [tmux](../commands/tmux.md)
- [terminal-multiplexing](../concepts/terminal-multiplexing.md)
