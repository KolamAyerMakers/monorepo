# Linux Foundations S8

Session: S8

Your own web service

<!-- end_slide -->

# Today's Story

The platform already serves your static homepage and report.

Today your own process serves those same files behind your service hostname.

Live route: tmux, manual server, Bash helper, systemd unit, endpoint checks, logs, and lingering.

<!-- end_slide -->

# Start With The Existing Site

On the classroom server, as your own account:

```bash
whoami
printf '%s\n' "$USER"
bash ~/scripts/site-check.sh "" maker-report.html
guide now
```

`$USER` must match your login. Read both checker results; repair missing pages before continuing. Keep the checker unchanged: it checks the static homepage and report, not the service hostname.

Run `guide now` before starting a quest and after practical work: it checks one task and shows the next on success. Otherwise, follow the feedback. Use `guide answer` when asked; `guide check` is an optional explicit check. Checks record evidence, not proof of HTTP 200.

<!-- end_slide -->

# Your Numeric Port

```bash
id -u
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
```

- `id -u` prints your numeric user ID (UID).
- `$(id -u)` runs a command and captures its output, like the curl capture in your checker.
- `$((...))` calculates an integer expression. UID `1234` gives port `11234`.
- `10000 + uid` is course routing policy, not a general Linux rule. Above `65535`, ask staff; do not choose a different port yourself.

<!-- end_slide -->

# Why tmux?

A foreground server occupies its shell until you stop it.

Tmux keeps a shell on the server while you detach, test from another shell, or reconnect after SSH drops.

It does not survive a server reboot, and host logout policy can still stop processes.

<!-- end_slide -->

# The tmux Lifecycle

Hands-on now: create a named session, then detach with `Ctrl-b`, release both keys, and press `d`.

```bash
tmux new -s workbench
```

Back in your original shell:

```bash
tmux ls
tmux attach -t workbench
```

Detach again, then end the session from your original shell:

```bash
tmux kill-session -t workbench
```

Detaching preserves the session; killing it ends the session.

<!-- end_slide -->

# Run The Server In tmux

Create the session again:

```bash
tmux new -s workbench
```

Inside tmux:

```bash
PORT="$((10000 + $(id -u)))"
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$HOME/public_html"
```

`--directory` selects the published files explicitly, regardless of your current directory. If that directory is missing, Python does not fall back to serving your shell's directory.

Keep `--bind 127.0.0.1`: only local clients, including the course reverse proxy, connect directly. If repeating this lab, stop `site.service` before starting a manual server on its port.

<!-- end_slide -->

# Test, Then Release The Port

Detach with `Ctrl-b d`. In your original shell:

```bash
PORT="$((10000 + $(id -u)))"
curl -I "http://127.0.0.1:$PORT/"
tmux attach -t workbench
```

Read the actual HTTP status. Each shell here computes its own `PORT`.

Inside tmux, press `Ctrl-C` to stop Python, then detach. Outside tmux:

```bash
tmux kill-session -t workbench
```

Detaching is not stopping. Release the port before systemd takes ownership.

Run `guide now`. If it advances from tmux to the manual-server task, run it again for that completed work. Follow any feedback, then continue at "Wrap service actions in shell functions".

<!-- end_slide -->

# Create The Helper

A function names commands inside `{ ... }`. Defining it does not run it; calling its name does. Functions also work inside scripts.

```bash
mkdir -p ~/bin
micro ~/bin/site.sh
```

Enter the complete script on the next slide. Save with `Ctrl-S`, quit with `Ctrl-Q`.

<!-- end_slide -->

# Complete `~/bin/site.sh`

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

<!-- end_slide -->

# Trace The Dispatch

```bash
chmod +x ~/bin/site.sh
~/bin/site.sh site_port
bash -x ~/bin/site.sh site_port
```

1. Bash reads the four function definitions without running their bodies.
2. The script's first argument is `site_port`. `"$@"` expands to the supplied arguments, keeping each a separate word.
3. Here there is one word, `site_port`, so Bash calls that function.
4. `id -u` supplies the UID, arithmetic adds `10000`, and `printf` prints the port. `-x` shows the expanded commands.

`serve` captures that printed number with `$(site_port)`; it is output, not the function's exit status. Keep `"$@"` quoted. This personal dispatcher can run other command names too; never feed it untrusted input.

<!-- end_slide -->

# Helper Actions

- `~/bin/site.sh serve` starts a foreground server, not systemd. Try it with local curl from another shell, then stop it with `Ctrl-C`.
- `~/bin/site.sh status` reads the user unit's state once the unit exists.
- `~/bin/site.sh stop` stops only that user unit, not a manual Python process.

The helper always selects `public_html`; an unchecked `cd` could fail and leave Python exposing unrelated files.

Run `guide now` and follow any feedback. Continue at the user-unit objective.

<!-- end_slide -->

# Create The User Unit

```bash
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
command -v python3
mkdir -p ~/.config/systemd/user
micro ~/.config/systemd/user/site.service
```

The course unit uses `/usr/bin/python3`. If the command reports a different installation, ask staff before proceeding.

Type the next unit, replacing `12345` with the number you printed. Do not type `$PORT` or shell arithmetic into the unit.

<!-- end_slide -->

# Complete `site.service`

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

`%h` means your home directory. Systemd requires `WorkingDirectory` to exist before starting Python; it cannot fall back to a different directory. `ExecStart` is not a Bash command line and does not evaluate `$()` or `$((...))`.

<!-- end_slide -->

# Hand Ownership To systemd

First stop every manual server with `Ctrl-C` in its terminal. Otherwise the user service cannot bind the occupied port.

```bash
systemctl --user daemon-reload
systemctl --user enable --now site.service
systemctl --user status site.service
```

- `daemon-reload` rereads unit files; it does not restart a process.
- `enable` arranges startup with your user manager's default target; `--now` starts it now.
- `Restart=on-failure` retries failures, not an intentional stop.
- Keep `--user`. This is your account's service, not a root service.

Read `Active:` honestly, including `inactive (dead)` or `failed`. Press `q` to leave a status pager. Diagnose failures before claiming it runs.

<!-- end_slide -->

# Request The Service

```bash
PORT="$((10000 + $(id -u)))"
curl -I "http://127.0.0.1:$PORT/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
journalctl --user -u site.service --no-pager -n 50
```

Read the status line from each response. Curl can exit `0` after a `404` or `502`; command completion is not HTTP success.

Local curl tests Python directly. The service hostname tests the reverse-proxy route from the server. Neither establishes access from your laptop's network.

Run `guide now` and follow any feedback before the journal exercise.

<!-- end_slide -->

# Watch A Request Arrive

In one SSH shell:

```bash
journalctl --user -u site.service -f
```

In another SSH shell, request the service through its public hostname:

```bash
curl -I "https://$USER.lf2607.kolamayermakers.org/"
```

Find the request and HTTP status in the journal. `-f` follows new messages; `Ctrl-C` stops the follower, not the service.

After stopping it, run `journalctl --user -u site.service --no-pager -n 20`, then `guide now` and follow any feedback. Continue with logout and browser checks even if the guide has moved to reinforcement.

<!-- end_slide -->

# Read Failures Before Repairing

- `Unit site.service not found`: check the file path and run `daemon-reload`.
- `Address already in use`: stop your manual server; do not kill another learner's process or pick a different port.
- `CHDIR`: restore the missing published directory through the existing site build.
- `EXEC`: inspect the executable path in the unit.
- Local HTTP works but public HTTP gives `502`: compare the numeric port, then ask staff about the proxy route.
- Name resolution fails: collect `host "$USER.lf2607.kolamayermakers.org"` and local curl output for staff.

After fixing a unit, run `systemctl --user daemon-reload`, then `systemctl --user restart site.service`, and repeat both service requests. Do not use `sudo` or change shared routing.

<!-- end_slide -->

# Who Controls Logout Survival?

```bash
loginctl show-user "$USER" -p Linger
systemctl --user show site.service -p MainPID -p ExecMainStartTimestamp
```

`Linger=yes` lets the user manager run without a login. With `Linger=no`, the manager and its services may stop after the last logout. Enabling a unit does not enable lingering.

Staff owns this policy. If `Linger=no`, request staff help with the output; learners do not run `sudo` or `loginctl enable-linger`.

Record the process ID and start timestamp before the logout experiment.

<!-- end_slide -->

# Test Logout Without Fooling Yourself

Close other SSH and browser-terminal sessions. From the last SSH shell, outside tmux, run `exit`.

While logged out, wait briefly and refresh the [service homepage](https://your-handle.lf2607.kolamayermakers.org/) in your laptop browser, replacing `your-handle`. Then reconnect using your own username:

```bash
ssh username@lf2607.kolamayermakers.org
systemctl --user status site.service
systemctl --user show site.service -p MainPID -p ExecMainStartTimestamp
```

An enabled unit can start again on login. Compare both `MainPID` and `ExecMainStartTimestamp` with your notes: a new process is a restart, not uninterrupted survival. A short observation is not a promise of indefinite uptime.

<!-- end_slide -->

# Preflight Both Public URLs

```bash
bash ~/scripts/site-check.sh "" maker-report.html
curl -I "https://lf2607.kolamayermakers.org/~$USER/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
systemctl --user show site.service -p ActiveState -p SubState
```

The unchanged checker still covers the static homepage and report. The two explicit curl commands request different hostnames, not the static URL twice.

Read `ActiveState` and `SubState`; `show` can report inactive or failed states without treating the query itself as a failure.

Replace `your-handle` and open the [static homepage](https://lf2607.kolamayermakers.org/~your-handle/), [report](https://lf2607.kolamayermakers.org/~your-handle/maker-report.html), and [service homepage](https://your-handle.lf2607.kolamayermakers.org/) in your laptop browser.

Server-side curl can use local host mappings. Browser access adds evidence from one outside network; a passing guide check alone proves neither HTTP 200 nor outside access.

<!-- end_slide -->

# Exit Goal

You have practiced tmux and a manual server, written the executable helper and numeric-port user unit, enabled and started it, inspected both service endpoints and logs, and explained lingering.

Keep the real response codes, service state, and any unresolved failure. An `inactive` or `failed` observation is valid evidence of a problem, not a reason to invent `active`.

<!-- end_slide -->

# Between-Session Practice Route

Use [the self-study guide](self-study.md) to finish any missing live core first.

Then use quests for extra tmux/log practice, a safe unit break and repair, health pages, and service notes. Keep the existing static checker instead of writing a second one.

<!-- end_slide -->

# Next Session

S9: polish and automation, on **2026-10-10**.

Bring `~/bin/site.sh`, `site.service`, your working site and report, and any unresolved URL or logout observations.

A service is a supervised process. The unit describes how to start it; the journal explains what happened.
