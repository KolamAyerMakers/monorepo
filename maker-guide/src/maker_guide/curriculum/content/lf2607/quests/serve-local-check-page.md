# Serve a local check page

Quest: serve-local-check-page

## Mission

Temporarily stop `site.service`, serve the site inside tmux, fetch it with `curl`, then restore the service.

## Commands You Will Use

- `systemctl --user`
- `tmux`
- `python3 -m http.server --bind 127.0.0.1`
- `curl`

## Steps

1. Stop the managed server with `systemctl --user stop site.service`.
2. Run `tmux new -s local-server`.
3. Inside tmux, set `PORT="$((10000 + $(id -u)))"` and run `cd ~/public_html`.
4. Start `python3 -m http.server "$PORT" --bind 127.0.0.1`.
5. Detach with `Ctrl-b d`, then run `tmux ls` in your original shell.
6. Recompute `PORT="$((10000 + $(id -u)))"` and fetch the site with `curl -I "http://127.0.0.1:$PORT/"`.
7. Run `tmux attach -t local-server`, then stop the server with `Ctrl-C`.
8. Detach with `Ctrl-b d`, then run `tmux kill-session -t local-server`.
9. Restore the managed server with `systemctl --user start site.service`.
10. Ask the guide to check your command history.

## Hints

1. Binding to `127.0.0.1` keeps the server local.
2. The temporary server and `site.service` cannot own the same port together.
3. The guide checks the stop, tmux lifecycle, server, curl, and service restart in order.

## If Check Fails

Finish the cleanup and restart `site.service` before asking again.

## Related Reading

- [python3 http.server](../commands/python3-http-server.md)
- [curl](../commands/curl.md)
- [systemctl](../commands/systemctl.md)
- [tmux](../commands/tmux.md)
- [manual web service](../concepts/manual-web-service.md)
- [sockets](../concepts/sockets.md)
