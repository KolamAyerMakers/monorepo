# Platform Reference

Use this page when a quest says "your server", "your local URL", "your service URL", "your static URL", "your port", IRC, Forgejo, or web SSH.

## Fixed Names

- SSH server: `lf2607.kolamayermakers.org`
- Web SSH: browser terminal for onboarding only
- Course static site host: `lf2607.kolamayermakers.org`
- IRC web client: [lf2607.kolamayermakers.org/irc/](https://lf2607.kolamayermakers.org/irc/)
- IRC channel: `#lf2607`
- Forgejo web UI: [lf2607.kolamayermakers.org/git/](https://lf2607.kolamayermakers.org/git/)
- Forgejo SSH host: `lf2607.kolamayermakers.org`
- Course bot: the guide.
- Static site source: `~/src/pages/`
- Static site output: `~/public_html/`
- User service unit path: `~/.config/systemd/user/site.service`
- User timer path: `~/.config/systemd/user/site-build.timer`

## guide checks

Run `guide now` before starting a quest and after practical work: it shows your current session objective or current task, checks one task, and shows the next on success; otherwise follow the feedback and try again. `guide today` and `guide next` do the same.

Use `guide answer 'your answer'` when asked. `guide check` is an optional explicit check. Ask the guide for help when stuck. In an IRC DM to `guide`, omit the `guide` prefix: send `now`, `today`, `next`, `answer <your answer>`, or `check`.

The guide checks explicit evidence such as command history, files, and answers, then records score and progress when the check passes. Chat responses can help you understand what to do, but progress requires a passing check. Read [scoring and rankings](scoring.md) for every score award, tier, ranking tie-breaker, and the points ledger.

The guide uses only course-approved evidence for checks. Do not paste secrets into IRC or chat: no passwords, private keys, access tokens, or private setup links.

## IRC Shape

Use your course username as your IRC nickname. Join `#lf2607` for public help, completion announcements, and coordination.

If your nickname is already in use, check whether you are still connected in another browser tab or client. If you need a temporary suffix, tell the instructor and switch back to your course username after the stale session disconnects.

The web IRC entry point is [lf2607.kolamayermakers.org/irc/](https://lf2607.kolamayermakers.org/irc/).

## Forgejo Shape

Forgejo is the class git server. `fj` and HTTPS Git use your configured class token.

- Web UI: [lf2607.kolamayermakers.org/git/](https://lf2607.kolamayermakers.org/git/)
- Repository name for site source: `src`
- Local source path: `~/src`
- Remote name: `origin`
- HTTPS remote shape: `https://lf2607.kolamayermakers.org/git/username/src.git`
- SSH remote shape: `git@lf2607.kolamayermakers.org:username/src.git`

```bash
fj repo create src
```

Use HTTPS first unless the instructor has confirmed your Forgejo SSH key setup. Verify the remote with `git remote -v` before pushing.

## Login Shape

```bash
ssh username@lf2607.kolamayermakers.org
```

The `new@lf2607.kolamayermakers.org` account is only the onboarding door. It creates your real account, prints the real SSH command, then disconnects.

Use the [password guide](passwords.md) when choosing or changing your classroom passphrase.

## Web SSH Graduation

Web SSH is an onboarding bridge. Use it when browser access is the only thing working or when you are still learning enough SSH to recover from mistakes.

Normal SSH is the target skill:

```bash
ssh username@lf2607.kolamayermakers.org
```

Web SSH recovery is available to Linux Foundations course members. It is not a graduation gate: use it whenever browser access is the only working path.

## Public URL Shapes

Static page URL:

```text
https://lf2607.kolamayermakers.org/~username/
```

User service URL:

```text
https://username.lf2607.kolamayermakers.org/
```

If the service URL does not resolve, collect local evidence before asking for routing help:

```bash
host "$(whoami).lf2607.kolamayermakers.org"
PORT="$((10000 + $(id -u)))"
curl -I "http://127.0.0.1:$PORT/"
systemctl --user status site.service
```

If local curl works and the public hostname does not resolve, bring those exact outputs to the instructor as a routing issue.

## Service Port Formula

In this course only, your personal service port is `10000 + uid`.

```bash
printf '%s\n' "$((10000 + $(id -u)))"
```

Use the result anywhere a service quest says `PORT`.

Ports are numeric. If your computed value is above `65535`, stop and ask the instructor because that account id does not fit this course port formula.

## Two Caddy Processes

Shared Caddy handles public HTTPS. It serves the static route directly from published files and proxies the service hostname to `127.0.0.1` at your assigned port. Your personal Caddy listens for plain HTTP on all interfaces; the classroom firewall blocks new direct external connections to that port. Same software, two processes with separate owners and lifecycles.

With your site already built in `~/public_html`, and no existing process using your assigned port, run in your own SSH shell:

```bash
PORT="$((10000 + $(id -u)))"
caddy file-server --listen ":$PORT" --root "$HOME/public_html" --access-log
```

Check the computed port against the range above before starting. Stop an existing manual server you own with `Ctrl-C`, or your managed backend with `systemctl --user stop site.service`, before transferring the port. Never stop an unknown listener.

For systemd, keep `WorkingDirectory=%h` and use `ExecStart=/usr/bin/caddy file-server --listen :12345 --root %h/public_html --access-log`, replacing `12345` with your numeric port. The stable working directory and explicit root let requests resolve the new tree after publication replaces `public_html`.

No Caddy configuration file is needed. Use `Ctrl-C` for the foreground process and `systemctl --user` for your unit, never `caddy stop` or `caddy reload`, which might target shared Caddy. Do not alter shared configuration. This setup uses neither a domain option nor directory browsing.

`--access-log` enables structured request logs in the terminal or service journal. Match `request.method`, `request.uri`, `status`, and time (`ts` in JSON); `request.remote_ip` may be the shared loopback proxy, not the visitor. A missing index returns `404` with browsing disabled even when the server is healthy. Keep only public files in the root: Caddy follows symlinks, so `--root` is not a filesystem sandbox.

## Proof Commands

```bash
whoami
pwd
ls -la ~
curl -I https://lf2607.kolamayermakers.org/~username/
git -C ~/src remote -v
systemctl --user status site.service
journalctl --user -u site.service --no-pager -n 50
```

## Docs Pointers

- [OpenSSH manual index](https://man.openbsd.org/ssh)
- [systemd service units](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)
- [systemd timers](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)
- [curl manual](https://curl.se/docs/manpage.html)
- [Caddy file-server CLI](https://caddyserver.com/docs/command-line#caddy-file-server)
