# Keep Your Server Running

Session: S8

2026-09-26

Your S7 server needed an open terminal. Who should own it now?

<!-- end_slide -->

# Start From What You Know

In your first SSH shell, with no existing server on your assigned port:

```bash
PORT="$((10000 + $(id -u)))"
caddy file-server --listen ":$PORT" --root "$HOME/public_html" --access-log
```

In a second SSH shell, compute `PORT` again and request it:

```bash
curl -i "http://127.0.0.1:$PORT/"
```

Reload the service homepage in your laptop browser.

If your own unit is already running, ask before interrupting it. Never stop an unknown process.

<!-- end_slide -->

# Hand Over The Lifecycle

Press `Ctrl-C` in the manual server's terminal before continuing. The service needs the same port.

```text
Before: SSH shell -> foreground personal Caddy
After:  user systemd manager -> personal Caddy described by site.service
```

Shared Caddy still handles public HTTPS and forwards to personal Caddy over loopback HTTP. Same software, two separate processes.

<!-- end_slide -->

# Describe The Command Once

A unit file describes one command. systemd runs it and keeps it running.

```bash
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
mkdir -p ~/.config/systemd/user
micro ~/.config/systemd/user/site.service
```

If the unit already exists, inspect it and agree to the changes first.

<!-- end_slide -->

# Your First Unit

```ini
[Unit]
Description=Personal website service

[Service]
WorkingDirectory=%h
ExecStart=/usr/bin/caddy file-server --listen :12345 --root %h/public_html --access-log
Restart=on-failure

[Install]
WantedBy=default.target
```

- Replace `12345` with your printed port. `ExecStart` is not Bash: no `$PORT`.
- `%h` is your home; `--root` points at the published site.
- `Restart=on-failure` restarts a crashed process, not an intentional stop.

<!-- end_slide -->

# Start Under Supervision

Confirm the manual server is stopped.

```bash
systemctl --user daemon-reload
systemctl --user enable --now site.service
systemctl --user status site.service --no-pager
```

- `enable --now` starts it now and on future logins.
- `daemon-reload` rereads unit files after an edit.
- Never use `caddy stop` or `caddy reload`: they can target shared Caddy.

<!-- end_slide -->

# Control Your Service

```bash
systemctl --user stop site.service
systemctl --user start site.service
systemctl --user restart site.service
journalctl --user -u site.service -n 20 --no-pager
```

Keep `--user`: this is your service, with no root access or `sudo`.

<!-- end_slide -->

# Ask The Real Server

```bash
curl -i "http://127.0.0.1:$PORT/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
```

Read the status and content, not just the exit code. Open the service homepage in your laptop browser and invite a peer.

An active service is not proof of a working page. If local access works and public access fails, ask the instructor.

<!-- end_slide -->

# Follow A Visitor

```bash
journalctl --user -u site.service -f
```

Ask a peer to open your service homepage and `/missing-s8-page.html`.

`--access-log` records `request.method`, `request.uri`, `status`, and a time. The visitor may appear as the shared proxy's loopback address.

Press `Ctrl-C`: only the log follower stops, not your service.

<!-- end_slide -->

# Publish While It Runs

Edit an existing page source, then:

```bash
build-website
```

Reload the page through the public route. Ask a peer to find the change.

Publishing replaces the site directory; the service keeps serving it because `--root` points at the published path. Do not restart the service.

<!-- end_slide -->

# One Reversible Break

Agree to a brief outage, then save your working unit:

```bash
BACKUP="$(mktemp -d "$HOME/site-service-backup.XXXXXX")"
cp ~/.config/systemd/user/site.service "$BACKUP/site.service"
printf '%s\n' "$BACKUP/site.service"
```

Continue only if the copy succeeded.

<!-- end_slide -->

# Make One Typo, Read Its Effect

Change only the executable path in `ExecStart`:

`/usr/bin/caddy` -> `/no/such/caddy`

```bash
systemctl --user stop site.service
micro ~/.config/systemd/user/site.service
systemctl --user daemon-reload
systemctl --user restart site.service
systemctl --user status site.service --no-pager
journalctl --user -u site.service --since "5 minutes ago" --no-pager
systemctl --user stop site.service
```

Read the real error. Expect an executable failure, often `203/EXEC`.

<!-- end_slide -->

# Restore And Verify

Review the difference, then restore:

```bash
diff -u "$BACKUP/site.service" ~/.config/systemd/user/site.service
cp -i "$BACKUP/site.service" ~/.config/systemd/user/site.service
systemctl --user daemon-reload
systemctl --user reset-failed site.service
systemctl --user restart site.service
systemctl --user status site.service --no-pager
```

Confirm local curl and public browser access again. A restart command alone is not recovery.

<!-- end_slide -->

# Logout Is A Separate Question

```bash
loginctl show-user "$USER" -p Linger
systemctl --user show site.service -p MainPID -p ExecMainStartTimestamp
```

Record the process ID and start time. `Linger=yes` lets your services run without a login; `enable` does not set it.

Close every SSH, browser terminal, editor, and tmux session: detaching is not logging out. Stay away past the wait agreed with the instructor, then open the page from your laptop before reconnecting.

After reconnecting, compare `MainPID` and `ExecMainStartTimestamp`. An enabled service can start on login; `active` alone proves nothing. If `Linger` is off, tell the instructor.

<!-- end_slide -->

# Leave A Working Handoff

Keep the working unit source copy and your service notes. No credentials; name peers only with consent.

You are done when the page loads through your service, its journal shows a real request, you recovered your own unit, and you know whether it survived logout.

<!-- end_slide -->

# Next: Automate It

S9: 2026-10-10. Bring your working service, source history, and notes.

Between sessions, use `guide` if you need help.
