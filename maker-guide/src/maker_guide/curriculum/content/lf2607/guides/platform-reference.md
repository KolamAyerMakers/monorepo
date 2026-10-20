# Classroom Platform Reference

These addresses and helpers belong to **this classroom**, not Linux in general. They may stop working after the server closes. For local practice, use [Continue at Home](continue-at-home.md).

## Accounts and addresses

Replace `username` with your course username:

| Purpose | Address |
|---|---|
| SSH login | `ssh username@lf2607.kolamayermakers.org` |
| New account registration | `ssh new@lf2607.kolamayermakers.org` |
| Browser registration | [Register](https://lf2607.kolamayermakers.org/register/) |
| Browser SSH/recovery | [Browser terminal](https://lf2607.kolamayermakers.org/ssh/) |
| Forgejo web interface | [Class repositories](https://lf2607.kolamayermakers.org/git/) |

Static homepage, served directly from published files:

```text
https://lf2607.kolamayermakers.org/~username/
```

Personal service homepage, requiring your web server:

```text
https://username.lf2607.kolamayermakers.org/
```

The `new` account creates your real account, prints its login command, then disconnects. Reconnect using your own username. Browser SSH is available for recovery as well as onboarding.

When choosing or changing your account password, see [Passwords](passwords.md).

## Files and publication

| Path or command | Meaning |
|---|---|
| `/docs` | Course material |
| `~/src` | Site project and local Git repository |
| `~/src/pages` | Editable Markdown pages |
| `~/public_html` | Generated HTML; replaced by publication |
| `build-website` | Classroom shortcut: build and publish the site |
| `/usr/local/bin/maker-guide-build-personal-website` | Installed executable for noninteractive builds |
| `~/.config/systemd/user/site.service` | Your web-server unit |
| `~/.config/systemd/user/site-build.service` | Scheduled generation/build task |
| `~/.config/systemd/user/site-build.timer` | That task's schedule |

Edit source and rebuild; do not edit generated HTML. The static URL reads published files directly. The service URL needs your personal server running too.

## Your assigned port

In this course, the port is **10000 + your numeric user ID**:

```bash
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
```

If above `65535`, stop and ask the instructor. Do not substitute a spare port or another learner's port. `PORT` exists only in the shell where you set it.

## Two Caddy processes

```text
static URL  → shared Caddy                 → public_html
service URL → shared Caddy → personal Caddy → public_html
```

Shared Caddy owns public HTTPS. For the service URL it is a reverse proxy, forwarding to your assigned loopback port over HTTP. Your personal Caddy answers those forwarded requests. Same software; separate owners and lifecycles.

Before a manual launch, stop your identified existing backend: `Ctrl-C` in its terminal, or `systemctl --user stop site.service` for the managed service. Never stop an unknown listener. With your site built and `PORT` set:

```bash
caddy file-server --listen ":$PORT" --root "$HOME/public_html" --access-log
```

The listener uses all interfaces; the classroom firewall blocks new direct external connections to learner ports. At home, use loopback-only `127.0.0.1:8080` instead.

- Keep the explicit published root. It is **not a sandbox**: symlinks can expose files outside it. Publish no credentials or private symlinks.
- Stop your foreground process with `Ctrl-C`. Do not use `caddy stop` or `caddy reload`; they may target shared Caddy.
- Do not add a domain option or directory browsing, alter shared routing, or bypass TLS verification.

For a user service, keep `WorkingDirectory=%h` and use a numeric port in `ExecStart`:

```ini
ExecStart=/usr/bin/caddy file-server --listen :12345 --root %h/public_html --access-log
```

Replace `12345` with your assigned port. `%h` means home; shell variables/arithmetic are not Bash-expanded here. A stable working directory and explicit root let new requests find the replaced publication tree.

## When the service URL fails

In your classroom shell:

```bash
host "$USER.lf2607.kolamayermakers.org"
curl -i --max-time 10 "http://127.0.0.1:$((10000 + $(id -u)))/"
systemctl --user status site.service
journalctl --user -u site.service --no-pager -n 30
```

For a manual server, inspect its terminal instead of expecting a systemd service. Distinguish no DNS answer, local connection refusal, an HTTP error, and wrong content. If local access works but public access fails, bring those results and the exact public error to the instructor.

Request logs identify method, URI, status, and time (`ts` in JSON). The client address may be the shared proxy, not the visitor. A `404` is an HTTP response; it is not proof the process stopped.

## Forgejo source repository

`fj` and HTTPS Git use your configured classroom token. Never put it in source files or the practice kit.

Local repository: `~/src`; class repository name: `src`; usual remote: `origin`.

HTTPS remote:

```text
https://lf2607.kolamayermakers.org/git/username/src.git
```

SSH remote, only after separate key setup:

```text
git@lf2607.kolamayermakers.org:username/src.git
```

`fj repo create src` creates an empty remote repository. Inspect `git remote -v` before adding/changing a remote, then push your intended branch. [Forgejo Publishing](../concepts/forgejo-publishing.md) has the full procedure.

## Optional classroom guide

| Command | Purpose |
|---|---|
| `guide` | Ask for help interactively |
| `guide now` | Show/check the current assigned task; advance after acceptance |
| `guide check` | Request a check explicitly |
| `guide answer 'your explanation'` | Submit an explanation when requested |

`guide today` and `guide next` are aliases for `guide now`. Recorded progress requires accepted evidence; help alone records no completion. See [Scoring](scoring.md). At home, use observations and worked answers instead of these classroom commands.
