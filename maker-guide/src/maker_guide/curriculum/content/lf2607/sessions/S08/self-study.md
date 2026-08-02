# S8 Self-Study Guide: Your Own Web Service

Session: S8

## Study Path

1. Compute your course service port with `10000 + uid`.
2. Create, detach from, list, reattach to, and end a tmux session.
3. Manually serve `~/public_html/` inside tmux.
4. Write helper functions in `~/bin/site.sh`.
5. Create `~/.config/systemd/user/site.service`.
6. Enable and start the service with `systemctl --user`.
7. Verify the local endpoint, the public service URL, and logout-survival behavior.
8. Debug with `journalctl --user` before changing random lines.

## Tmux And The Manual Server

A foreground server occupies its shell. Tmux keeps that shell available on the server when you detach or SSH disconnects.

Create a named session:

```bash
tmux new -s workbench
```

Inside tmux, start the server:

```bash
PORT="$((10000 + $(id -u)))"
cd ~/public_html
python3 -m http.server "$PORT" --bind 127.0.0.1
```

Press `Ctrl-b`, release both keys, then press `d`. Back in your original shell, list the session and test the server:

```bash
tmux ls
PORT="$((10000 + $(id -u)))"
curl -I "http://127.0.0.1:$PORT/"
```

Shell variables do not cross shells. Recompute `PORT` in every shell that uses it. This port formula is course infrastructure policy, not a general Linux rule.

Return to the server:

```bash
tmux attach -t workbench
```

Press `Ctrl-C` to stop the server, detach again with `Ctrl-b d`, then end the tmux session:

```bash
tmux kill-session -t workbench
```

Detaching preserves the session. `tmux kill-session` ends it. Tmux survives an SSH disconnect, not a server reboot. The manual server owns its port while it is running, so stop it before enabling `site.service` or systemd will fail with `Address already in use`.

## Minimal `~/bin/site.sh`

```bash
#!/bin/bash
set -euo pipefail

site_port() {
  printf '%s\n' "$((10000 + $(id -u)))"
}

serve() {
  cd "$HOME/public_html"
  python3 -m http.server "$(site_port)" --bind 127.0.0.1
}

status() {
  systemctl --user status site.service
}

stop() {
  systemctl --user stop site.service
}

"$@"
```

Create the directory first with `mkdir -p ~/bin`.

Then run `chmod +x ~/bin/site.sh` and test `~/bin/site.sh site_port`.

## Minimal `site.service`

Create `~/.config/systemd/user/site.service` after `mkdir -p ~/.config/systemd/user`.

```ini
[Unit]
Description=Personal website service

[Service]
WorkingDirectory=%h/public_html
ExecStart=/usr/bin/python3 -m http.server 12345 --bind 127.0.0.1
Restart=on-failure

[Install]
WantedBy=default.target
```

Replace `12345` with `10000 + uid` from the command above. Systemd does not run shell arithmetic in `ExecStart` unless you explicitly run a shell, so use the number.

## Service Lifecycle

Stop the manual foreground server before this step. The systemd user service will bind the same localhost port.

```bash
PORT="$((10000 + $(id -u)))"
systemctl --user daemon-reload
systemctl --user enable --now site.service
systemctl --user status site.service
journalctl --user -u site.service --no-pager -n 50
curl -I "http://127.0.0.1:$PORT/"
curl -I "https://$(whoami).lf2607.kolamayermakers.org/"
```

The local URL proves your process answers on the server. The public service URL proves the reverse proxy can reach it.

## Lingering Check

Lingering is the systemd setting that lets user services survive logout. On the shared course server, staff controls the setting; learners should verify behavior, not run privileged lingering commands.

```bash
loginctl show-user "$USER" -p Linger
exit
ssh username@lf2607.kolamayermakers.org
systemctl --user status site.service
```

If `Linger=no` but your service is expected to survive logout, bring the `loginctl` and `systemctl` output to the instructor. Do not use `sudo`.

## Troubleshooting

- `Unit site.service not found`: check the path, then run `systemctl --user daemon-reload`.
- `Failed at step EXEC`: check the `ExecStart` path with `command -v python3`.
- `Address already in use`: stop the old process or fix the port.
- Public service URL is `502`: service is not running, wrong port, or proxy cannot reach it. Run local `curl -I` and `systemctl --user status site.service` before changing the unit.
- Public service hostname does not resolve: run the DNS and local-service checks from the platform reference, then bring the evidence to the instructor.
- `systemctl` asks for root service state: you forgot `--user`.
- `tmux new -s workbench` says the session exists: run `tmux ls`, then attach instead of creating it again.
- Tmux warns about nested sessions: you are already inside tmux. Detach before creating another session.
- `tmux ls` says no server is running: no tmux session exists. Create one again.

## Safe Break Lab

Change `ExecStart=/usr/bin/python3` to `ExecStart=/no/such/python`, reload, restart, then read the error. Restore the original line immediately after you understand the failure.

## Proof Checklist

- You can create, detach from, list, reattach to, and end a tmux session.
- `~/bin/site.sh` has `site_port`, `serve`, `stop`, and `status` functions.
- `site.service` exists and is loaded by user systemd.
- Local curl against `127.0.0.1:PORT` succeeds.
- Public service URL returns an HTTP response or you have DNS evidence from the platform reference.
- `loginctl show-user "$USER" -p Linger` has been checked, and you know whether staff must enable lingering.
- `journalctl --user -u site.service` shows service logs.
- You can recover from one broken unit file.

## Docs Pointers

- Run `man tmux` and read the [tmux command card](../../commands/tmux.md).
- Read [Platform Reference](../../guides/platform-reference.md) before choosing URL or port values.
- Read [Python http.server](https://docs.python.org/3/library/http.server.html).
- Read [systemd service units](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html).
- Read [systemctl](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html) and [journalctl](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html).
- Read [Terminal Multiplexing](../../concepts/terminal-multiplexing.md), [Service](../../concepts/service.md), [Sockets](../../concepts/sockets.md), [Process](../../concepts/process.md), [Logging](../../concepts/logging.md), and [Lingering](../../concepts/lingering.md) for the deeper model behind sessions, services, and logs.
