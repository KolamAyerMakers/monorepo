# Linux Foundations S8

Session: S8

Your own web service

<!-- end_slide -->

# Today's Story

The platform served your first URL.

Today your own process serves the second one.

First keep a foreground server in tmux. Then let systemd manage it.

<!-- end_slide -->

# Why tmux?

A foreground server occupies its shell until you stop it.

Tmux lets the server keep running while you return to your original shell, test it, or reconnect after SSH drops.

Tmux survives an SSH disconnect, not a server reboot.

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

Create `workbench`, then run this inside it:

```bash
PORT="$((10000 + $(id -u)))"
cd ~/public_html
python3 -m http.server "$PORT" --bind 127.0.0.1
```

Detach with `Ctrl-b d`. In your original shell, recompute `PORT` and test the server:

```bash
PORT="$((10000 + $(id -u)))"
curl -I "http://127.0.0.1:$PORT/"
```

Reattach, stop the server with `Ctrl-C`, detach, then kill `workbench`.

<!-- end_slide -->

# Move From Manual To Managed

Hands-on now: make the same server survive without tmux.

```bash
systemctl --user status site.service
journalctl --user -u site.service -f
loginctl show-user "$USER" -p Linger
```

<!-- end_slide -->

# Exit Goal

Learners use tmux for a foreground server, then run a persistent user-managed service and know how lingering affects logout survival.
<!-- end_slide -->

# Between-Session Practice Route

Highly recommended after class or for catch-up:

Use the guide throughout class and between sessions: run `guide now` for your current session objective; after you complete it, it shows your current quest. Submit prompted answers with `guide answer 'your answer'`, and run `guide check` after practical work. A passing check records your progress.

1. Repeat the tmux create, detach, list, attach, and kill lifecycle.
2. Write helper functions in `~/bin/site.sh`.
3. Create `site.service` as a systemd user service, managed by your account rather than root.
4. Watch logs while curling the service.
5. Break the service safely and read the error.
6. Fix, restart, and verify both URLs.

<!-- end_slide -->

# Service Mental Model

A service is a supervised process.

The unit file describes how to start it.

The journal explains what happened.
