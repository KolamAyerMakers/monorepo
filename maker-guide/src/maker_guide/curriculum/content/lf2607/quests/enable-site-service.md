# Enable site.service

Quest: enable-site-service

## Mission

Create, enable, and start your user `site.service` for the service hostname, then inspect its local and public HTTP responses.

## Commands You Will Use

- `id -u`
- `mkdir`
- `micro`
- `systemctl --user`
- `curl`

## Steps

Stop any manual Python server with `Ctrl-C` in its terminal before systemd takes the same port. Detaching from tmux does not stop it. Your existing `~/public_html` must contain the built site; do not create a new source project for this quest.

Compute the port and open the unit:

```bash
id -u
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
command -v python3
mkdir -p ~/.config/systemd/user
micro ~/.config/systemd/user/site.service
```

`$(id -u)` captures your numeric UID; `$((...))` adds `10000`. This is the course's assigned routing formula. If the result is above `65535`, ask staff; do not choose another number. The course unit uses `/usr/bin/python3`; if `command -v` reports a different installation, ask staff before proceeding.

Enter this unit, replacing `12345` with the numeric result you printed. If the unit already exists from class, inspect and correct it:

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

`%h` expands to your home directory. Systemd requires `WorkingDirectory=%h/public_html` to exist before it starts Python, so it cannot silently serve another directory. `ExecStart` does not run through Bash: type the number, not `$PORT`, `$()`, or `$((...))`.

Save with `Ctrl-S`, quit with `Ctrl-Q`, and start the unit with the manual server stopped:

```bash
systemctl --user daemon-reload
systemctl --user enable --now site.service
systemctl --user status site.service
PORT="$((10000 + $(id -u)))"
curl -I "http://127.0.0.1:$PORT/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
journalctl --user -u site.service --no-pager -n 50
```

Read the actual state and both HTTP status lines. Local curl tests Python; the service hostname tests the proxy route from this server. Curl may exit `0` after an HTTP error. Replace `your-handle` in the [service homepage](https://your-handle.lf2607.kolamayermakers.org/) and open it in your laptop browser for evidence of access from an outside network.

Run `guide check` after the work. It checks the numeric-port unit and observed commands for the local and public service endpoints, not independent proof that HTTP 200 or outside access succeeded. Report unresolved failures honestly.

## Hints

1. This is a systemd user service: managed by your user account, not by root or the system administrator.
2. Keep `--user` in every systemctl command.
3. `daemon-reload` rereads unit files; it does not restart a running process. After changing an existing unit, also run `systemctl --user restart site.service`.
4. `enable --now` arranges startup with your user manager and starts the unit now. `Restart=on-failure` retries failures, not intentional stops.
5. Enablement does not enable lingering. Run `loginctl show-user "$USER" -p Linger`; if it says `Linger=no` and the service should survive logout, request staff help. Do not use `sudo` or enable lingering yourself.

## If Check Fails

Confirm the file path, `WorkingDirectory`, numeric port, and `--bind 127.0.0.1`. Repeat the enable/start and both endpoint commands above after repairing the cause.

- `Address already in use`: stop your manual server, then restart the unit; do not kill another learner's process.
- `CHDIR`: inspect and restore the existing published directory rather than removing `WorkingDirectory`.
- `EXEC`: inspect the executable path and journal.
- `inactive` or `failed`: report the actual state and read the journal before claiming success.
- Local HTTP works but the service hostname returns `502`: compare the assigned port, then bring remaining proxy problems to staff.
- Name resolution fails: collect `host "$USER.lf2607.kolamayermakers.org"` and local curl output for staff. Do not alter shared routing or disable TLS checks.

## Related Reading

- [id -u](../commands/id-u.md)
- [systemctl](../commands/systemctl.md)
- [systemd user services](../concepts/systemd-user-services.md)
- [S8 logout experiment](../sessions/S08/self-study.md#lingering-check)
- [preflight both URLs](preflight-both-urls.md)
