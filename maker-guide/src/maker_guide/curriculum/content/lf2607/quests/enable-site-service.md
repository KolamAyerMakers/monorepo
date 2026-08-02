# Enable site.service

Quest: enable-site-service

## Mission

Create and enable your user `site.service` for the second URL.

## Commands You Will Use

- `id -u`
- `mkdir`
- `micro`
- `systemctl --user`
- `curl`

## Steps

1. Run `id -u` and compute your course service port as `10000 + uid`.
2. Run `mkdir -p ~/.config/systemd/user`.
3. Create `~/.config/systemd/user/site.service`.
4. Add this unit, replacing `12345` with your numeric port:

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

5. Run `command -v python3` and confirm `/usr/bin/python3` exists.
6. Run `systemctl --user daemon-reload`.
7. Run `systemctl --user enable --now site.service`.
8. Run `curl -I http://127.0.0.1:<port>/` with your numeric port.
9. Ask the guide to check the unit file and the successful service commands.

## Hints

1. This is a systemd user service: managed by your user account, not by root or the system administrator.
2. Keep `--user` in every systemctl command.
3. Systemd unit files need the numeric port, not `$PORT`.

## If Check Fails

Confirm the file path is exactly `~/.config/systemd/user/site.service`, then check that `ExecStart` contains `/usr/bin/python3 -m http.server`, your computed numeric port, and `--bind 127.0.0.1`. The guide also needs to see the successful `systemctl --user enable --now site.service` and `curl -I http://127.0.0.1:<port>/` commands.

## Related Reading

- [id -u](../commands/id-u.md)
- [systemctl](../commands/systemctl.md)
- [systemd user services](../concepts/systemd-user-services.md)
