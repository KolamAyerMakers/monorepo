# Write site helper functions

Quest: write-site-helper-functions

## Mission

Create executable `~/bin/site.sh` with subcommands for your local site server.

## What The Script Should Achieve

You are building one reusable command for the second URL workflow. Instead of retyping long server and service commands, you should be able to run:

- `~/bin/site.sh site_port`: print your assigned course port, computed as `10000 + uid`.
- `~/bin/site.sh serve`: serve `~/public_html` on your assigned loopback port, regardless of the caller's directory.
- `~/bin/site.sh status`: show the user `site.service` status after you create it.
- `~/bin/site.sh stop`: stop the user `site.service` after you create it.

`serve` is a foreground manual server, not a command to start systemd. `status` and `stop` become useful after [enable-site-service](enable-site-service.md) creates the unit. `stop` stops that unit, not a manual Python process.

## Commands You Will Use

- `mkdir`
- `micro`
- `chmod`
- `python3 -m http.server --bind 127.0.0.1`
- `id -u`
- `systemctl --user`

## Steps

1. Run `mkdir -p ~/bin`.
2. Run `micro ~/bin/site.sh` and enter the complete helper below. If it already exists from class, inspect and correct it rather than creating a different version.
3. Save with `Ctrl-S` and quit with `Ctrl-Q`.
4. Run the self-check, then `guide check` for file and executable-permission evidence. This does not prove the HTTP endpoint works.

## Complete Helper

```bash
#!/bin/bash

site_port() {
  printf '%s\n' "$((10000 + $(id -u)))"
}

serve() {
  python3 -m http.server "$(site_port)" --bind 127.0.0.1 --directory "$HOME/public_html"
}

status() {
  systemctl --user status site.service
}

stop() {
  systemctl --user stop site.service
}

"$@"
```

A function names the commands inside `{ ... }`; the body runs only when called. `site_port` prints output that `serve` captures. A function's exit status is a separate success/failure number, not a way to print its result.

`$(id -u)` runs `id -u` and captures your numeric UID. `$((...))` performs integer arithmetic on that output: UID `1234` gives `11234`. The formula is course routing policy; if your port exceeds `65535`, ask staff rather than choosing another number.

`--directory "$HOME/public_html"` explicitly selects the published files. An unchecked `cd` can fail and leave Python serving unrelated files from the caller's directory. With `--directory`, a missing `public_html` does not fall back to that directory. Keep the loopback bind; the course proxy connects locally.

## Dispatch Trace

For `~/bin/site.sh site_port`:

1. Bash reads the four function definitions without running them.
2. The script's first argument, `$1`, is `site_port`.
3. The final `"$@"` expands to the supplied arguments, one word per argument. Here the one word is `site_port`, so Bash calls that function.
4. The function captures the UID, adds `10000`, and prints the number.

Keep `"$@"` quoted so arguments containing spaces remain separate arguments. This personal dispatcher can run other command names too; it is not an allowlist and must not receive untrusted input.

## Self-Check

Make it executable, print the port, and use `-x` to see the expanded commands:

```bash
chmod +x ~/bin/site.sh
~/bin/site.sh site_port
bash -x ~/bin/site.sh site_port
```

If the user unit is already running, stop it with `systemctl --user stop site.service` before the manual test. Run `~/bin/site.sh serve` in one SSH shell. In another:

```bash
PORT="$((10000 + $(id -u)))"
curl -I "http://127.0.0.1:$PORT/"
```

Inspect the HTTP status, then press `Ctrl-C` in the server shell. Do not leave the manual server running before enabling or starting `site.service`. If you stopped an existing unit for this test, restore it with `systemctl --user start site.service` and repeat the request.

After the unit exists, `~/bin/site.sh status` reports its actual state, including inactive or failed. `~/bin/site.sh stop` deliberately stops it; start it again with `systemctl --user start site.service` when it should be serving.

## Hints

1. Bash functions let a script give names to repeated command sequences.
2. `$()` captures output; `$((...))` calculates a number. They solve different problems.
3. Use `--directory` instead of depending on `cd` succeeding before Python starts.

## If Check Fails

Open `~/bin/site.sh`, compare all four functions and the final quoted dispatch with the complete helper, and rerun `chmod +x ~/bin/site.sh`. If HTTP gives `404`, inspect the published files; do not remove `--directory` to make Python serve somewhere else.

## Related Reading

- [python3 http server](../commands/python3-http-server.md)
- [mkdir](../commands/mkdir.md)
- [chmod](../commands/chmod.md)
- [bash-functions](../concepts/bash-functions.md)
- [manual-web-service](../concepts/manual-web-service.md)
- [systemctl](../commands/systemctl.md)
