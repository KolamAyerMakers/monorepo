# systemd User Services

## Core Idea

User services let your account run supervised processes without root access.

## Practice Alone

Create this file at `~/.config/systemd/user/site.service`, replacing `14567` with your computed port from the platform reference:

```ini
[Unit]
Description=Personal course site service

[Service]
WorkingDirectory=%h/public_html
ExecStart=/usr/bin/python3 -m http.server 14567 --bind 127.0.0.1

[Install]
WantedBy=default.target
```

Then operate it with user-scope systemd commands:

```bash
systemctl --user daemon-reload
systemctl --user enable --now site.service
systemctl --user status site.service
journalctl --user -u site.service --no-pager -n 50
```

Do not drop `--user`. Without it, you are asking for system services, not your account's services.

## Done When

`systemctl --user status site.service` shows an active service you understand.

## Go Deeper

- [Service](service.md) distinguishes network services, systemd services, user services, and system services.
- [Logging](logging.md) explains how logs support debugging.
- [Userspace](userspace.md) explains why your service runs as your user rather than root.
- [Process basics](process-basics.md) explains the running process behind the service.
- [Kernel](kernel.md) explains what still belongs to the operating system kernel.
- [systemctl](../commands/systemctl.md) and [journalctl](../commands/journalctl.md) are the command cards for operating services.
- [Platform reference](../guides/platform-reference.md) gives the service port formula and public URL shapes.
