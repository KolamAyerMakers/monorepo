# Keep a tmux workbench

Quest: keep-tmux-workbench

## Mission

Create a named tmux session, detach without ending it, list it, reattach, then end it.

## Commands You Will Use

- `tmux`

## Steps

1. Run `tmux new -s quest-workbench`.
2. Detach with `Ctrl-b d`.
3. Run `tmux ls`.
4. Reattach with `tmux attach -t quest-workbench`.
5. Detach again with `Ctrl-b d`.
6. Run `tmux kill-session -t quest-workbench`.
7. Ask the guide to check your work.

## Hints

1. Press `Ctrl-b`, release both keys, then press `d`.
2. Detach does not kill the session.
3. The guide needs to see create, list, attach, and kill-session commands for `quest-workbench`.

## If Check Fails

- If `quest-workbench` already exists, run `tmux kill-session -t quest-workbench`, then create it again.
- If `tmux ls` says no server is running, create `quest-workbench` again.
- If tmux warns about nesting, detach from the current session first.

## Related Reading

- [tmux](../commands/tmux.md)
- [terminal-multiplexing](../concepts/terminal-multiplexing.md)
