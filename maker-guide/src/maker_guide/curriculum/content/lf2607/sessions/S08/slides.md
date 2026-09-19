# Keep Your Server Running

Session: S8

2026-09-26

Your S7 server needed an open terminal. Who should own its lifecycle now?

<!-- end_slide -->

# Restart The Manual Server

In your first SSH shell, with no existing server on your assigned port:

```bash
PORT="$((10000 + $(id -u)))"
caddy file-server --listen ":$PORT" --root "$HOME/public_html" --access-log
```

In a second SSH shell, compute `PORT` again and request it with `curl -i --max-time 10 "http://127.0.0.1:$PORT/"`. Reload the service homepage in your laptop browser.

If your own unit is already running, inspect it and agree to the interruption before stopping it for this exercise. Never stop an unknown process.

<!-- end_slide -->

# Hand Over The Lifecycle

Press `Ctrl-C` in the manual server's terminal before continuing. The user service needs the same port.

```text
Before: SSH shell -> foreground personal Caddy
After:  user systemd manager -> personal Caddy described by site.service
```

Route: restart and handover (25 min), unit and preservation (45 min), requests and logs (25 min), break (10 min), repair (35 min), logout and handoff (40 min).

Shared Caddy still handles HTTPS and forwards to personal Caddy over loopback HTTP. Same software, two separate processes; no `--domain` or shared configuration changes.

Enabling a unit alone does not promise survival after logout.

<!-- end_slide -->

# Prepare Your Own Unit

```bash
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
/usr/bin/caddy version
mkdir -p ~/.config/systemd/user
micro ~/.config/systemd/user/site.service
```

If the computed port exceeds `65535` or Caddy is unavailable, ask the instructor. If this unit already exists, inspect it, preserve a unique backup, and agree to changes before editing; use the [self-study preservation steps](self-study.md#2-create-the-user-unit).

Type the next unit with your printed number in place of `12345`.

<!-- end_slide -->

# Use A Stable Working Directory

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

`%h` means your home. The publisher replaces `public_html`, so keep the working directory at home and serve the explicit `--root` path. The root is not a sandbox; keep private files and symlinks to them out.

`--listen :12345` listens on all interfaces; the classroom firewall blocks new direct external connections to your port. `ExecStart` is not Bash: use your literal numeric port, not `$PORT` or shell arithmetic. No helper script is needed.

<!-- end_slide -->

# Start Under Supervision

Confirm the manual server is stopped, then:

```bash
systemctl --user daemon-reload
systemctl --user enable --now site.service
systemctl --user status site.service --no-pager
```

`daemon-reload` rereads unit definitions; it does not restart a process. `enable --now` enables startup with your user manager and starts now. If you edited an already-running unit, also restart it.

`Restart=on-failure` retries failures, not an intentional stop. Keep `--user`; no root service or `sudo`.

Never use `caddy stop` or `caddy reload`: they can target shared Caddy. Control your service with `systemctl --user` only.

<!-- end_slide -->

# Ask The Real Server

```bash
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
curl -I --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
```

Read the status and content, not just the command's exit code. Then open the service homepage in your laptop browser and invite a peer.

An active process is not proof of a working page. If local access works and public access fails, compare the port and ask the instructor about the route.

<!-- end_slide -->

# Preserve The Unit Now

Keep a source copy outside the published pages:

```bash
mkdir -p ~/src/services
cp -i ~/.config/systemd/user/site.service ~/src/services/site.service
git -C ~/src status
git -C ~/src diff -- services/site.service
git -C ~/src diff --cached
```

Read an existing destination before consenting to replacement, and inspect new files in the editor. If unrelated work is staged, preserve it and pause. Otherwise stage only `services/site.service`, review the complete staged diff, and commit the working unit now.

<!-- end_slide -->

# Follow A Visitor

In one SSH shell:

```bash
journalctl --user -u site.service -f
```

Ask a peer to open your service homepage and `/missing-s8-page.html`. `--access-log` records `request.method`, `request.uri`, `status`, and a time or timestamp (`ts` in JSON). Journal formatting may differ from the foreground terminal. Shared Caddy's loopback address is not the visitor's identity.

Press `Ctrl-C`. Which process stopped? Only the log follower, not your web service. Two SSH shells are enough; tmux is optional.

<!-- end_slide -->

# Publish While It Runs

Add the service start/stop instructions to `~/src/pages/setup.md`, then:

```bash
build-website
```

After a successful build, reload the setup page through both public routes. Ask a peer to find the change. Do not restart the service.

The stable `WorkingDirectory=%h` plus explicit `--root %h/public_html` matters here: publishing replaces the directory, not just individual file contents.

<!-- end_slide -->

# Agree To One Reversible Break

After the break, use only your working `site.service`. Agree to the brief outage and keep the same SSH shell for backup and recovery.

```bash
BACKUP="$(mktemp -d "$HOME/site-service-backup.XXXXXX")"
cp ~/.config/systemd/user/site.service "$BACKUP/site.service"
printf '%s\n' "$BACKUP/site.service"
```

Record the path. Continue only if the copy succeeded. Existing backups stay untouched. Inspect custom content with `systemctl --user cat site.service`; if this is not the simple course unit, get help choosing a safe exercise first.

<!-- end_slide -->

# Make One Typo, Read Its Effect

Stop your unit, then edit only the executable path in `ExecStart` from `/usr/bin/caddy` to `/no/such/caddy`. Keep every other setting.

```bash
systemctl --user stop site.service
micro ~/.config/systemd/user/site.service
systemctl --user daemon-reload
systemctl --user restart site.service
systemctl --user status site.service --no-pager
journalctl --user -u site.service --since "5 minutes ago" --no-pager
systemctl --user stop site.service
```

Read the actual error before repairing. Expect an executable failure, often `203/EXEC`; retries may also hit a start limit. The final stop ends retries. Do not change ports, files, permissions, or another learner's processes.

<!-- end_slide -->

# Restore, Reload, Restart

Review the difference first. If it contains more than your deliberate typo, preserve the other changes and ask before copying.

```bash
diff -u "$BACKUP/site.service" ~/.config/systemd/user/site.service
cp -i "$BACKUP/site.service" ~/.config/systemd/user/site.service
systemctl --user daemon-reload
systemctl --user reset-failed site.service
systemctl --user restart site.service
systemctl --user status site.service --no-pager
```

Consent to restoring your saved unit at the copy prompt. `reset-failed` clears failure and retry-limit state. Confirm local curl and public browser access again; a successful restart command alone is not recovery.

<!-- end_slide -->

# Separate Enablement From Lingering

```bash
loginctl show-user "$USER" -p Linger
systemctl --user show site.service -p MainPID -p ExecMainStartTimestamp
```

Record the process ID and start timestamp somewhere available after logout. `Linger=yes` allows the user manager to run without a login. `enable` does not set it.

If lingering is off or the instructor has not confirmed the logout policy and wait interval, ask the instructor before claiming survival. Learners do not enable lingering or use `sudo`.

<!-- end_slide -->

# Close All Login Sessions

Close every SSH connection, browser terminal, remote editor login, and any other login for your account. End any optional tmux shells; detaching is not logging out. From the last SSH shell, run `exit`.

Stay logged out for the interval agreed with the instructor, long enough to exceed the configured logout delay. Reload the service homepage freshly in the laptop browser and ask your peer to request it too. Do not reconnect first.

Then reconnect and compare `MainPID` and `ExecMainStartTimestamp`. An enabled service can start on login; `active` afterward alone proves nothing about the logged-out interval.

<!-- end_slide -->

# Leave A Working Handoff

Update `setup.md` with your observed failure, diagnosis, repair, logout result, and a peer's useful feedback. No credentials; name peers only with consent.

Build and browse the notes, then review and commit only the intended source files. Keep the working unit source copy, not the deliberately broken version or private backups.

Success: a peer gets the page through your supervised backend, requests appear in its journal, you recover your own unit, and you can explain the observed logout result without claiming untested uptime.

<!-- end_slide -->

# Next: Automate It. Hand It Over.

S9: 2026-10-10.

Bring your working service, source history, setup notes, and any unresolved routing or logout issue. We will automate report updates and have a peer use your operating instructions.

Use the [self-study route](self-study.md) for complete examples and the repair decision table.

<!-- end_slide -->

# Between Sessions

Use `guide` if you need help between sessions.
