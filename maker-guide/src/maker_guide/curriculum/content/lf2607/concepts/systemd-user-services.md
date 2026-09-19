# systemd User Services

## Core Idea

User services let your account run supervised processes without root access.

## Practice Alone

Use a Linux login with a running systemd user manager, `/usr/bin/caddy`, curl, and `ss`. This independent example serves only a generated test page, not an existing website. Check the tools, user manager, and candidate loopback port first:

```bash
command -v caddy systemctl journalctl curl ss
/usr/bin/caddy version
systemctl --user list-units --type=service
ss -H -ltn 'sport = :18080'
```

Stop if a tool or the user manager is unavailable; ask the machine administrator rather than using `sudo`. Port `18080` is an example, not a reserved assignment. If `ss` lists a listener, choose another unused unprivileged port and replace `18080` in every example below. Do not stop or kill another user's process. A free-port observation is not a reservation: if startup later reports `Address already in use`, inspect again.

Create a new demo directory. If `~/sample-web` already exists, inspect and preserve it rather than overwriting its files; continue only with a new directory or one you have confirmed is disposable.

```bash
mkdir "$HOME/sample-web"
printf '<!doctype html>\n<title>Sample web</title>\n<h1>Sample web works</h1>\n' > "$HOME/sample-web/index.html"
mkdir -p ~/.config/systemd/user
systemctl --user cat sample-web.service
```

`No files found` for the new unit is expected. If the unit already exists, inspect its file and any drop-ins before proceeding; do not replace unrelated work. Save this complete file at `~/.config/systemd/user/sample-web.service` using your editor:

```ini
[Unit]
Description=Standalone sample web server

[Service]
WorkingDirectory=%h
ExecStart=/usr/bin/caddy file-server --listen 127.0.0.1:18080 --root %h/sample-web --access-log

[Install]
WantedBy=default.target
```

`%h` expands to your absolute home path. Keep the working directory stable and select the served directory explicitly: if a publisher replaces that directory, new requests resolve the current path rather than remaining in an old working directory. Never omit `--root` here, which would expose home-directory content. Only serve intended public files; Caddy follows symlinks, so this root is not a security sandbox. Loopback restricts direct connections, but a configured reverse proxy could still expose the listener.

This serves plain HTTP without a configuration file. `file-server` disables the admin API; operate the process with `systemctl --user`, never `caddy stop` or `caddy reload`, which might target another Caddy process. A separate shared Caddy can handle public HTTPS: same software, different process.

Then operate it with user-scope systemd commands:

```bash
systemctl --user daemon-reload
systemctl --user enable --now sample-web.service
systemctl --user status sample-web.service --no-pager
curl -i --max-time 5 http://127.0.0.1:18080/
journalctl --user -u sample-web.service --no-pager -n 50
```

Look for HTTP `200`, the generated `Sample web works` heading, and the matching request in the journal. `--access-log` supplies structured request fields such as `request.method`, `request.uri`, `status`, and `ts` in JSON. An active unit alone does not prove the content is correct. With browsing disabled, a missing index at `/` returns `404`, just like an absent file; repair the intended content rather than broadening the root.

After editing a unit, run `daemon-reload` and restart it to apply the definition to the process. Normal content edits need neither. Do not drop `--user`: without it, you are asking for system services, not your account's services. Enablement does not guarantee logout survival; see [Lingering](lingering.md).

Stop and disable this practice service when finished:

```bash
systemctl --user disable --now sample-web.service
curl -i --max-time 5 http://127.0.0.1:18080/
```

With no other listener, the last request should fail to connect, not return an HTTP error. If it still answers, inspect the port before acting; never kill an unidentified process.

## Done When

You can start the sample, inspect its actual response and request log, explain the explicit serving path, and stop it without affecting other users.

## Go Deeper

- [Service](service.md) distinguishes network services, systemd services, user services, and system services.
- [Logging](logging.md) explains how logs support debugging.
- [Userspace](userspace.md) explains why your service runs as your user rather than root.
- [Process basics](process-basics.md) explains the running process behind the service.
- [Kernel](kernel.md) explains what still belongs to the operating system kernel.
- [systemctl](../commands/systemctl.md) and [journalctl](../commands/journalctl.md) are the command cards for operating services.
