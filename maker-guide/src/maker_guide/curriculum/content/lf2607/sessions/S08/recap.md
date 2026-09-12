# S8 Recap: Your Own Service

Session: S8

## Core Idea

A website can be served by a process you own. The static URL and your service hostname serve the same published files through different server processes.

## Remember

- Tmux keeps a foreground shell available when you detach or reconnect, but not across a reboot; host logout policy can still stop it.
- Shell child processes may be terminated when the shell exits. An ordinary foreground shell is not reliable service supervision.
- A user service is supervised independently by your user manager. `enable --now` enables and starts it, but does not enable lingering.
- `serve` uses `--directory "$HOME/public_html"` so a failed directory change cannot expose unrelated files. Keep the loopback bind.
- `$()` captures command output; `$((...))` calculates a number. Quoted `"$@"` dispatches the helper's supplied arguments without splitting them again.
- Logs are not decoration. They are evidence.
- `systemctl --user status` is the first question when a service misbehaves.

## Live Core

The live milestone includes:

- Create, detach from, list, reattach to, and end a tmux session.
- Start a manual server for `public_html`, request its local endpoint, and stop it before systemd takes the same port.
- Create executable `~/bin/site.sh` with `site_port`, `serve`, `status`, `stop`, and quoted `"$@"`; trace `~/bin/site.sh site_port`.
- Create `~/.config/systemd/user/site.service` with `WorkingDirectory=%h/public_html`, the numeric result of `10000 + uid` (not the expression), and `--bind 127.0.0.1`; reload, enable, and start it.
- Inspect local and public service responses, read the actual unit state, and match a request to journal output.
- Explain lingering, ask staff for help if it is disabled, and distinguish uninterrupted operation from a restart on login.

## Final Preflight

On the classroom server:

```bash
bash ~/scripts/site-check.sh "" maker-report.html
PORT="$((10000 + $(id -u)))"
curl -I "http://127.0.0.1:$PORT/"
curl -I "https://lf2607.kolamayermakers.org/~$USER/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
systemctl --user show site.service -p ActiveState -p SubState
journalctl --user -u site.service --no-pager -n 50
loginctl show-user "$USER" -p Linger
```

The unchanged checker checks the static homepage and report, not the service endpoint. Read each HTTP status and report `inactive` or `failed` honestly when that is what systemd says; repair comes next. Curl can exit `0` after an HTTP error.

Local curl tests Python; the service hostname tests the proxy route from the server, possibly using local host mappings. Replace `your-handle` and open the [static homepage](https://lf2607.kolamayermakers.org/~your-handle/), [report](https://lf2607.kolamayermakers.org/~your-handle/maker-report.html), and [service homepage](https://your-handle.lf2607.kolamayermakers.org/) in your laptop browser for outside-access evidence.

Staff owns lingering: if `Linger=no`, request help, not `sudo`. For a logout experiment, record `systemctl --user show site.service -p MainPID -p ExecMainStartTimestamp` before logout and compare it after reconnecting. Close other logins and check the browser while logged out; `active` after reconnecting alone can be a newly started service.

## Optional Reinforcement

Use the S8 quests for repeated tmux/log practice, a safe unit break and repair, health pages, and service notes. Helper and unit creation are already live core. Run `guide now` for your current session objective; after you complete it, it shows your current quest. Submit prompted answers with `guide answer 'your observation'`, and run `guide check` after practical work. A passing check records evidence, not independent proof of HTTP 200 or outside access.

## Can You Explain This?

- Why can tmux survive an SSH disconnect but not a server reboot?
- What process serves your second URL?
- What happens at the final `"$@"` in `~/bin/site.sh site_port`?
- Why must the unit contain a numeric port rather than `$PORT` or shell arithmetic?
- Why does `daemon-reload` matter after editing a unit file?
- Where do service errors appear?
- Why can `active` after reconnecting fail to prove logout survival?

## Keep

Keep `~/bin/site.sh` and `~/.config/systemd/user/site.service`; they become part of the final demo and README.

## Full Autonomy

Use [S8 Self-Study Guide: Your Own Web Service](self-study.md) for the tmux workflow, helper script, unit file, port formula, systemctl lifecycle, journal checks, and safe break lab.

## Next Session

S9 is on **2026-10-10**: polish and automation. Bring the helper, unit, site and report, and any unresolved service observations.
