# Enable site.service

Quest: enable-site-service

## Mission

Hand your working backend to a systemd user service. A peer should be able to load the page, and publishing a source change should not require restarting the process.

## Prepare Safely

Use your own classroom account and existing published site. Stop your manual Caddy server with `Ctrl-C` in its terminal before systemd takes the same port. Detaching from optional tmux does not stop a process. Do not stop another learner's server.

Staff must preflight the route, Caddy installation, user manager, and `Linger`. Enabling the unit does not promise logout survival. No `sudo`, shared routing changes, or TLS bypasses are needed.

```bash
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
/usr/bin/caddy version
mkdir -p ~/.config/systemd/user
ls -la ~/.config/systemd/user
```

The assigned port is `10000 + uid`. If the result exceeds `65535` or Caddy is missing, ask staff. Do not choose another port.

If `site.service` exists, inspect it and its overrides with `systemctl --user cat site.service`. Agree to the edits before changing it, and use the [unique-backup instructions](../sessions/S08/self-study.md#2-create-the-user-unit). Preserve custom content and existing backups; do not replace a different application with this template.

## Create The Unit

Open `micro ~/.config/systemd/user/site.service`. For a new unit, enter this complete content, replacing `12345` with your printed numeric port. For an existing course unit, make only the agreed changes.

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

`%h` expands to your home. The publisher replaces `public_html`, so keep `WorkingDirectory=%h` and the explicit `--root %h/public_html`. Personal Caddy listens for plain HTTP on all interfaces; the classroom firewall blocks new direct external connections to its port. A separate shared Caddy handles public HTTPS and proxies to `127.0.0.1` at that port. Same software, two processes; do not add `--domain`. The root is not a sandbox: Caddy follows symlinks, so publish only public files.

No Caddy configuration file is needed. `file-server` disables the admin API. Use `systemctl --user` for this unit, never `caddy stop` or `caddy reload`, which might target the shared proxy. `--access-log` records requests in the journal.

`ExecStart` is not a Bash command: use the literal number, not `$PORT`, `$()`, or arithmetic. Save with `Ctrl-S` and quit with `Ctrl-Q`.

## Start And Visit

With the manual server stopped:

```bash
systemctl --user daemon-reload
systemctl --user enable --now site.service
systemctl --user status site.service --no-pager
PORT="$((10000 + $(id -u)))"
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
curl -I --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
```

`daemon-reload` rereads definitions, not running processes. If you edited an already-running unit, also use `systemctl --user restart site.service`. `enable --now` enables startup with the user manager and starts now. `Restart=on-failure` retries failures, not intentional stops.

Read the real state, status, and content. If startup fails, read `journalctl --user -u site.service --no-pager -n 50`. An active unit or curl exit code alone does not establish page success.

Replace `your-handle` in the [service homepage](https://your-handle.lf2607.kolamayermakers.org/) and open it from your laptop. Invite a peer. Edit an existing source page, run `build-website`, and reload after success without restarting the service. Confirm the new content appears through both public routes.

## Preserve And Continue

Use [Preserve the working unit](../sessions/S08/self-study.md#4-preserve-the-working-unit) to keep `~/src/services/site.service` outside public pages and commit only that intended source copy after review. Improve linked `setup.md` with the lifecycle instructions. Preserve existing files and unrelated staged work; no credentials or private backups in Git.

Run `loginctl show-user "$USER" -p Linger` and discuss the result with staff. Learners do not enable lingering themselves. Follow the [complete logout experiment](../sessions/S08/self-study.md#9-test-logout-survival): close all account logins, wait past the staff-confirmed logout delay, request the page while logged out, then compare process identity and start time after reconnecting. `active` after login alone can be a fresh start.

## If It Does Not Work

- `Address already in use`: stop your own manual server, not an unknown process; do not change the assigned port.
- `EXEC`: inspect the executable path and journal.
- `CHDIR`: the stable home working directory is missing or inaccessible; ask staff about account access rather than broadening permissions.
- Local HTTP `404`: inspect the explicit root and successful build, not just service state. A missing index makes `/` return `404` with browsing disabled; repair the output rather than enabling browsing.
- Local access works but public access fails: compare the numeric port and bring actual results to staff. DNS/TLS errors are not HTTP `502`.

## Related Reading

- [Watch service logs](watch-service-logs.md)
- [Systemctl](../commands/systemctl.md)
- [Systemd user services](../concepts/systemd-user-services.md)
