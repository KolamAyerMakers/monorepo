# S8 Recap: Keep Your Server Running

Session: S8

Date: 2026-09-26

## What Changed

In S7 your SSH shell owned a foreground personal Caddy process. In S8 you restarted it, stopped it to release the port, then gave the same job to your systemd user manager. Shared Caddy still handles public HTTPS and forwards to personal Caddy over loopback HTTP. Same software, two separate processes; the static route still serves files independently.

## The Unit Contract

The installed file is `~/.config/systemd/user/site.service`:

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

Replace `12345` with your actual numeric result of `10000 + uid`. If the result exceeds `65535`, ask the instructor rather than choosing another port. `ExecStart` is not Bash; it does not calculate shell expressions.

`%h` means your home directory. The publisher replaces `public_html`, so the working directory stays at `%h` and personal Caddy follows the explicit `--root %h/public_html` path on new requests. The listener uses all interfaces; the classroom firewall blocks new direct external connections to the port. Do not add `--domain`; shared HTTPS is already configured. The root is not a sandbox: keep private files and symlinks to them out. Without `--browse`, a missing index does not produce an automatic directory listing.

## Lifecycle Decisions

| Change or question | Action |
| --- | --- |
| New unit | `systemctl --user daemon-reload`, then `systemctl --user enable --now site.service` |
| Installed unit edited | Reread with `daemon-reload`, then restart the service |
| Page source edited | `build-website`, then browser reload, no service restart |
| Need to stop it | `systemctl --user stop site.service` |
| Need to see its state | `systemctl --user status site.service --no-pager` |
| Need recent errors or requests | `journalctl --user -u site.service --no-pager -n 50` |
| Need new log lines live | `journalctl --user -u site.service -f` |

`Restart=on-failure` retries failures, not intentional stops. `Ctrl-C` stops a journal follower, not the service. Keep `--user`; no `sudo`, shared routing changes, or TLS bypasses.

`file-server` disables its admin API. Never use `caddy stop` or `caddy reload`: they can target shared Caddy's admin endpoint. Stop the supervised personal process with `systemctl --user stop site.service` only.

## Observe Real Outcomes

An active unit alone does not prove that the page works. Request personal Caddy locally, then load the public service page in the laptop browser:

```bash
PORT="$((10000 + $(id -u)))"
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
curl -I --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
```

Replace `your-handle` in the [service homepage](https://your-handle.lf2607.kolamayermakers.org/) and [static homepage](https://lf2607.kolamayermakers.org/~your-handle/). Confirm recognizable content through both routes. `--access-log` records structured fields `request.method`, `request.uri`, `status`, and a timestamp or time (`ts` in JSON). Match them to a peer's requests; journal and terminal formatting can differ. Personal Caddy may log shared Caddy's loopback address, not the peer's address. Shared Caddy is a server to the browser and a client to personal Caddy. A missing path can yield `404` while the service is healthy.

## Repair Safely

Agree to any interruption first. Back up your own working unit to a unique private directory, preserving previous backups and custom content. The class exercise changes only `/usr/bin/caddy` to `/no/such/caddy`, reads the executable failure (often `203/EXEC`), and stops retries. Restore only after comparing the backup with the broken file and consenting to replacement; preserve any unrelated edits.

After restoration, use `daemon-reload`, `reset-failed`, and `restart`, then confirm local and public access. `reset-failed` clears failure and retry-limit state; it does not repair configuration. Do not leave a deliberate break behind or interfere with another learner's processes. The [self-study repair lab](self-study.md#7-break-and-read-the-error) contains the complete backup and recovery sequence.

## Logout Is A Separate Experiment

The instructor must confirm lingering and the logout observation interval:

```bash
loginctl show-user "$USER" -p Linger
systemctl --user show site.service -p MainPID -p ExecMainStartTimestamp
```

Enabling a unit arranges startup with the user manager. `Linger=yes` lets that manager run without a login; enablement alone does not set it or guarantee logout survival. Ask the instructor about the policy. Learners do not enable lingering themselves.

Record process identity and start time. Close **all** SSH, browser-terminal, remote editor, and other account logins; end any optional tmux shells rather than merely detaching. Stay logged out past the delay confirmed by the instructor, and request the public page freshly from your laptop or a peer before reconnecting. Compare identity and start time after reconnecting. A service can start again on login, so `active` afterward alone is not proof of survival. Report only the interval you observed, not indefinite uptime.

## Keep

Keep the working unit source copy at `~/src/services/site.service`, outside published pages. Keep operational notes in linked `setup.md`: numeric port, lifecycle, observed failure and repair, logout result, and useful peer feedback with consent before naming anyone. Build and browse updates without restarting. Review and commit only intended source files as they are created; preserve unrelated work and exclude credentials, private backups, and generated output.

Success is a page a peer can load, requests you can locate in the journal, a failure you can diagnose and repair, and an honest explanation of logout behavior. Tmux and helper functions are optional; no `site.sh` dispatcher is needed.

## Next Session

S9: **2026-10-10**, Automate It. Hand It Over. Bring your working service, source history, setup notes, and unresolved issues. Use the [self-study route](self-study.md) for complete examples.
