# Watch service logs

Quest: watch-service-logs

## Mission

Use `journalctl --user -u site.service -f` while making a request with `curl`.

## Commands You Will Use

- `tmux`
- `journalctl --user`
- `curl`

## Steps

1. Run `tmux new -s logs`.
2. Inside tmux, run `journalctl --user -u site.service -f`.
3. Detach with `Ctrl-b d`.
4. Run `curl` against your second URL from the original shell.
5. Run `tmux attach -t logs` and watch the new log line.
6. Stop `journalctl` with `Ctrl-C`, then detach with `Ctrl-b d`.
7. Run `tmux kill-session -t logs`.
8. Ask the guide to check command history.

## Hints

1. `-f` follows new logs.
2. A request should produce a service log line.
3. The guide checks the named tmux session, journal follow, curl, reattach, and cleanup in order.

## If Check Fails

Repeat the named tmux workflow and end the `logs` session before asking again.

## Related Reading

- [journalctl](../commands/journalctl.md)
- [tmux](../commands/tmux.md)
- [service logs](../concepts/service-logs.md)
