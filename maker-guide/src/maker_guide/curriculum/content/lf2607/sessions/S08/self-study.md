# S8 Self-Study Guide: Your Own Web Service

Session: S8

## Study Path

1. Reuse the existing static checker and compute your course service port.
2. Create, detach from, list, reattach to, and end a tmux session.
3. Manually serve `~/public_html/` inside tmux.
4. Write helper functions in `~/bin/site.sh`.
5. Create `~/.config/systemd/user/site.service`.
6. Enable and start the service with `systemctl --user`.
7. Inspect local and public service responses and read the journal.
8. Explain lingering, check logout behavior, and open both public sites in a browser.

The helper, unit, endpoint observations, logs, and lingering explanation are live core. The safe break lab below is reinforcement, not a replacement for creating the service.

## Preflight

Reconnect to the classroom server as your own account:

```bash
whoami
printf '%s\n' "$USER"
bash ~/scripts/site-check.sh
guide now
```

`$USER` should match your login. If not, ask staff before constructing URLs. You already have the site, report generator, and static checker; do not recreate or overwrite them. Read both checker results and repair missing pages using the [existing checker workflow](../S06/self-study.md#repair-a-missing-report).

Keep `~/scripts/site-check.sh` unchanged. It checks your static homepage and report, not your service hostname. The platform serves the static URL; your new process will serve the same `~/public_html` files through the reverse proxy at the service hostname.

Run `guide now` before starting a quest and after practical work. It checks one task and shows the next on success; otherwise follow the feedback. Use `guide answer 'your observation'` when asked; `guide check` is an optional explicit check. A passing check records file and command observations, not independent proof of HTTP 200 or outside reachability.

## Port Arithmetic

```bash
id -u
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
```

- `id -u` prints your numeric user ID (UID), not your username.
- `$(id -u)` runs a command and substitutes its stdout, just like the curl capture in your checker.
- `$((...))` evaluates integer arithmetic. For UID `1234`, adding `10000` gives port `11234`.
- `PORT=...` stores that result; `"$PORT"` supplies it as one argument.

This formula is course routing policy, not a general Linux rule. If the result exceeds `65535`, ask staff instead of choosing a different port. Each shell below computes its own `PORT`.

## Tmux And The Manual Server

A foreground server occupies its shell. Tmux keeps that shell available on the server when you detach or SSH disconnects. It does not survive a server reboot, and host logout policy can still stop processes.

Create a named session:

```bash
tmux new -s workbench
```

Inside tmux, start the server. If repeating this lab after creating `site.service`, first stop that unit with `systemctl --user stop site.service` so the port is free.

```bash
PORT="$((10000 + $(id -u)))"
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$HOME/public_html"
```

`--directory` selects the published directory explicitly; a missing directory never makes Python serve the caller's current directory instead. Without this option, an unchecked `cd` could fail and expose unrelated files. Keep `--bind 127.0.0.1`: the course reverse proxy connects locally, so Python does not need to listen on every interface.

Press `Ctrl-b`, release both keys, then press `d`. Back in your original shell, list the session and test the server:

```bash
tmux ls
PORT="$((10000 + $(id -u)))"
curl -I "http://127.0.0.1:$PORT/"
```

Read the HTTP status line. Curl can exit `0` after a `404`; a completed request is not necessarily a successful page.

Return to the server:

```bash
tmux attach -t workbench
```

Press `Ctrl-C` to stop the server, detach again with `Ctrl-b d`, then end the tmux session:

```bash
tmux kill-session -t workbench
```

Detaching preserves the session; `tmux kill-session` ends it. The manual server owns its port while running, so stop Python before enabling `site.service` or systemd will fail with `Address already in use`.

Run `guide now`. If it advances from tmux to "Start a web server manually", run it again for that completed lab work. Follow any feedback, then continue at "Wrap service actions in shell functions".

## Minimal `~/bin/site.sh`

A function gives a name to commands inside `{ ... }`. Defining it does not run its body; calling its name does. Functions can live inside a script as well as in an interactive shell.

```bash
mkdir -p ~/bin
micro ~/bin/site.sh
```

Enter this complete helper, save with `Ctrl-S`, and quit with `Ctrl-Q`:

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

- `site_port` prints the computed number. Its output is not its exit status: `return 11234` would not print a port.
- `serve` captures that output with `$(site_port)` and starts the foreground server using an explicit directory.
- `status` reads the user unit's state; it may report that no unit exists until the next step.
- `stop` stops the user unit, not a manually started Python process.

Make it executable and trace a call:

```bash
chmod +x ~/bin/site.sh
~/bin/site.sh site_port
bash -x ~/bin/site.sh site_port
```

For `~/bin/site.sh site_port`, Bash first reads the definitions. The script's `$1` is `site_port`; the final `"$@"` expands to that one argument and calls the function. The function captures `id -u`, adds `10000`, and prints the number. `bash -x` shows the expanded commands on stderr as they run.

`"$@"` keeps each supplied argument a separate word, including arguments containing spaces. It is not the same as unquoted `$@`. This minimal personal dispatcher can also run other command names; it is not an allowlist and must not receive untrusted input.

With the port free, run `~/bin/site.sh serve` in one SSH shell. In another, recompute `PORT` and run `curl -I "http://127.0.0.1:$PORT/"`. Stop the helper's foreground server with `Ctrl-C` before proceeding.

Run `guide now` and follow any feedback. Continue when it shows the service-unit objective.

## Minimal `site.service`

```bash
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
command -v python3
mkdir -p ~/.config/systemd/user
micro ~/.config/systemd/user/site.service
```

The course unit uses `/usr/bin/python3`. If `command -v` reports a different installation, ask staff before proceeding. Enter this unit, replacing `12345` with your printed numeric port:

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

- `%h` is systemd's home-directory specifier. `WorkingDirectory=%h/public_html` must exist before Python can start; a missing directory stops startup rather than selecting some other directory.
- `ExecStart` is not run by Bash. Use the literal number, not `$PORT`, `$()`, or `$((...))`.
- `Restart=on-failure` retries a failed process, not an intentional stop.
- `WantedBy=default.target` lets enablement attach this unit to your user manager's normal startup target.

## Service Lifecycle

Stop the manual foreground server before this step. The systemd user service will bind the same localhost port.

```bash
PORT="$((10000 + $(id -u)))"
systemctl --user daemon-reload
systemctl --user enable --now site.service
systemctl --user status site.service
curl -I "http://127.0.0.1:$PORT/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
journalctl --user -u site.service --no-pager -n 50
```

`daemon-reload` rereads units but does not restart a running process. `enable` arranges future startup with your user manager, and `--now` also starts the unit now. Keep `--user`; no root service or `sudo` is needed.

Read `Active:` and report the actual state, including `inactive (dead)` or `failed`. A nonzero status-command exit is normal for a stopped or failed unit. Press `q` if the status opens a pager. Repair is the next step, not a reason to invent `active (running)`.

Inspect each HTTP status line. A response from the local URL tests Python directly; a response from the public service URL tests the reverse-proxy route from this server. An HTTP error is still a response, and neither command proves access from an outside network.

Run `guide now` and follow any feedback before continuing with the journal exercise.

## Follow The Journal

In one SSH shell:

```bash
journalctl --user -u site.service -f
```

In another SSH shell, request the public service route:

```bash
curl -I "https://$USER.lf2607.kolamayermakers.org/"
```

Match the request and status to the new journal line. `-f` follows new messages. `Ctrl-C` stops only the log follower; the service stays under systemd. The [log quest](../../quests/watch-service-logs.md) adds a named tmux workflow for the same observation.

After stopping the follower, run `journalctl --user -u site.service --no-pager -n 20` to read the saved request lines, then `guide now` and follow any feedback. Finish the lingering and browser checks below even if the guide has moved to optional reinforcement.

## Lingering Check

`Linger=yes` lets your user manager run without a login. With `Linger=no`, the manager and its services may stop after the last logout. Unit enablement and lingering are separate settings. On the shared course server, staff controls lingering.

```bash
loginctl show-user "$USER" -p Linger
systemctl --user show site.service -p MainPID -p ExecMainStartTimestamp
```

If `Linger=no` but the service should survive logout, request staff help with this output. Do not use `sudo` or run `loginctl enable-linger` yourself.

For a logout experiment, record `MainPID` and `ExecMainStartTimestamp` in your notes while the unit is running. Close other SSH and browser-terminal logins, then leave the last SSH shell outside tmux:

```bash
exit
```

While logged out, wait briefly and refresh the [service homepage](https://your-handle.lf2607.kolamayermakers.org/) in your laptop browser, replacing `your-handle`. Then reconnect with your own username and compare:

```bash
ssh username@lf2607.kolamayermakers.org
systemctl --user status site.service
systemctl --user show site.service -p MainPID -p ExecMainStartTimestamp
```

An enabled service can start again when you reconnect. `active` after login alone does not prove logout survival: compare both the process ID and start timestamp. If they changed, report a restart. A brief successful observation is not proof of indefinite uptime; other logins and logout delays can also mask shutdown.

## Preflight Both Public URLs

```bash
bash ~/scripts/site-check.sh
curl -I "https://lf2607.kolamayermakers.org/~$USER/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
systemctl --user show site.service -p ActiveState -p SubState
```

Keep the original checker: its static homepage and report checks remain useful, but it does not check the service hostname. The explicit curl commands above request the static homepage and the service homepage separately. Read the codes, not just curl's exit status or the guide result.

`show` reports `ActiveState` and `SubState` without treating an inactive or failed state as a failed query. Record those states honestly; repair them before claiming the service works.

Server-side curl can use local host mappings, so its public-hostname response is not proof of outside access. Replace `your-handle` and open the [static homepage](https://lf2607.kolamayermakers.org/~your-handle/), [report](https://lf2607.kolamayermakers.org/~your-handle/maker-report.html), and [service homepage](https://your-handle.lf2607.kolamayermakers.org/) in your laptop browser. Verify the content, not only headers. That adds evidence from one outside network, not every visitor's network.

## Troubleshooting

- `Unit site.service not found`: check the path, then run `systemctl --user daemon-reload`.
- `Failed at step EXEC`: check the `ExecStart` path with `command -v python3`.
- `Failed at step CHDIR`: `WorkingDirectory` is missing or inaccessible. Inspect `~/public_html` and repair the existing site build; do not remove `WorkingDirectory` to bypass the error.
- `Address already in use`: stop your manual server in its terminal. If the port in the unit is wrong, restore your assigned number; do not choose another port or kill another learner's process.
- `inactive (dead)`: if it should be running, start it with `systemctl --user start site.service`, then inspect status and HTTP responses again.
- Public service URL is `502`: the service may be stopped, on the wrong port, or unreachable by the proxy. Check local curl, numeric port, and service status first; bring remaining routing problems to staff.
- Public service hostname does not resolve: run `host "$USER.lf2607.kolamayermakers.org"` and the local-service checks, then bring the evidence to staff. Do not change DNS, shared proxy configuration, or TLS verification.
- `systemctl` asks for root service state: you forgot `--user`.
- `tmux new -s workbench` says the session exists: run `tmux ls`, then attach instead of creating it again.
- Tmux warns about nested sessions: you are already inside tmux. Detach before creating another session.
- `tmux ls` says no server is running: no tmux session exists. Create one again.

## Safe Break Lab

Only after the working service is verified, edit your own unit with `micro ~/.config/systemd/user/site.service`. Temporarily replace just `/usr/bin/python3` in `ExecStart` with `/no/such/python`, keeping the remaining arguments. Then:

```bash
systemctl --user daemon-reload
systemctl --user restart site.service
journalctl --user -u site.service --no-pager -n 50
systemctl --user stop site.service
```

Read the specific failure; stop the unit to end retries. Immediately restore `/usr/bin/python3` and your numeric port, then recover:

```bash
systemctl --user daemon-reload
systemctl --user reset-failed site.service
systemctl --user restart site.service
systemctl --user status site.service
PORT="$((10000 + $(id -u)))"
curl -I "http://127.0.0.1:$PORT/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
```

`reset-failed` clears the failure state and any retry-limit counter from the deliberate break. Rereading the unit alone is not enough: restart and inspect both responses. Do not leave a broken unit for the next session.

## Proof Checklist

- You can create, detach from, list, reattach to, and end a tmux session.
- You started a manual loopback server for `public_html`, requested it, and stopped it before systemd took the port.
- Executable `~/bin/site.sh` has all four functions, an explicit serving directory, and quoted `"$@"` dispatch that you can trace.
- `site.service` has the numeric assigned port and `WorkingDirectory=%h/public_html`; you enabled and started it with `--user`.
- You inspected local and public service response codes, not merely command exit statuses.
- The unchanged static checker covers the homepage and report, and you inspected both public sites in your laptop browser.
- You read a request in the service journal and reported the actual service state.
- You checked lingering, know that staff owns it, and can distinguish a restart on login from logout survival.
- Record unresolved failures honestly and ask staff for help. Guide evidence does not certify HTTP 200 or outside access.
- Optional reinforcement: break and recover your own unit without leaving it broken.

## Docs Pointers

- Run `man tmux` and read the [tmux command card](../../commands/tmux.md).
- Read [Platform Reference](../../guides/platform-reference.md) before choosing URL or port values.
- Read [Python http.server](https://docs.python.org/3/library/http.server.html).
- Read [systemd service units](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html).
- Read [systemctl](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html) and [journalctl](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html).
- Read [Terminal Multiplexing](../../concepts/terminal-multiplexing.md), [Service](../../concepts/service.md), [Sockets](../../concepts/sockets.md), [Process](../../concepts/process.md), [Logging](../../concepts/logging.md), and [Lingering](../../concepts/lingering.md) for the deeper model behind sessions, services, and logs.
- Read [Bash Functions](../../concepts/bash-functions.md) for function arguments and output versus return status.

## Next Session

S9 is on **2026-10-10**: polish and automation. Keep the helper, unit, working site and report, and any unresolved URL or logout observations.
