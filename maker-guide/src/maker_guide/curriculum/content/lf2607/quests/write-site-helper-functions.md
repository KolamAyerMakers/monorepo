# Write site helper functions

Quest: write-site-helper-functions

## Mission

Create executable `~/bin/site.sh` with subcommands for your local site server.

## What The Script Should Achieve

You are building one reusable command for the second URL workflow. Instead of retyping long server and service commands, you should be able to run:

- `~/bin/site.sh site_port`: print your assigned course port, computed as `10000 + uid`.
- `~/bin/site.sh serve`: serve `~/public_html` on `127.0.0.1:<your-port>`.
- `~/bin/site.sh status`: show the user `site.service` status after you create it.
- `~/bin/site.sh stop`: stop the user `site.service` after you create it.

`serve` is useful before systemd exists. `status` and `stop` become useful after `enable-site-service` creates `site.service`.

## Commands You Will Use

- `mkdir`
- `micro`
- `chmod +x`
- `python3 -m http.server --bind 127.0.0.1`
- `id -u`
- `systemctl --user`

## Steps

1. Run `mkdir -p ~/bin`.
2. Create `~/bin/site.sh`.
3. Add functions named `site_port`, `serve`, `status`, and `stop`.
4. Make `site_port` compute and print your assigned port.
5. Make `serve` switch to `~/public_html` and start the Python HTTP server on `127.0.0.1` and that port.
6. Make `status` show the user `site.service` state.
7. Make `stop` stop the user `site.service`.
8. Add dispatch logic so the first argument chooses which function runs.
9. Run `chmod +x ~/bin/site.sh`.
10. Run `~/bin/site.sh site_port` and confirm it prints a number.
11. Ask the guide to check the file.

## Self-Check

These quick commands should make sense after your script exists:

```bash
~/bin/site.sh site_port
~/bin/site.sh status
~/bin/site.sh stop
```

To test `serve`, run `~/bin/site.sh serve` in one terminal, curl the printed port from another terminal, then press `Ctrl-C` in the server terminal. Do not leave it running before enabling `site.service`.

Do not expect `status` or `stop` to be interesting until `enable-site-service` creates `site.service`. They still need to be present now because the script is becoming your service control tool.

## Hints

1. Bash functions let a script give names to repeated command sequences.
2. `site_port` needs `id -u`; `serve` needs `python3 -m http.server --bind 127.0.0.1`; `status` and `stop` need `systemctl --user`.
3. One simple dispatch pattern is to let the script run the function named by its arguments.

## If Check Fails

Open `~/bin/site.sh`, check each required function against the self-check commands, and rerun `chmod +x ~/bin/site.sh`.

## Related Reading

- [python3 http server](../commands/python3-http-server.md)
- [mkdir](../commands/mkdir.md)
- [chmod](../commands/chmod.md)
- [bash-functions](../concepts/bash-functions.md)
- [manual-web-service](../concepts/manual-web-service.md)
- [systemctl](../commands/systemctl.md)
