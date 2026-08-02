# Service

## Core Idea

A service is a long-running or supervised capability that other programs or users can rely on.

## Meanings You Will See

- Network service: a process listening for network requests, such as SSH, HTTP, or SMTP.
- systemd service: a unit managed by systemd, such as `site.service`.
- System service: a root-managed or administrator-managed service for the whole machine.
- User service: a systemd service managed by your user account with `systemctl --user`.

## Course Examples

```bash
PORT="$((10000 + $(id -u)))"
systemctl --user status site.service
journalctl --user -u site.service --no-pager -n 50
curl -I "http://127.0.0.1:$PORT/"
```

Your personal web service is both a network service and a systemd user service: it listens for HTTP requests on the course-assigned port and is supervised by your per-user systemd instance.

## What A Service Needs

- A command to start.
- A user account and permissions.
- Files or directories it needs to read.
- A port if it is a network service.
- Logs for diagnosis.
- A restart or recovery policy if supervised.

## Common Confusions

- `service` does not always mean systemd. A service can be any useful long-running process.
- A systemd service can be a one-shot task, not only a daemon.
- A user service is not a root service. Use `systemctl --user`.
- A process can listen locally while the public reverse proxy still fails.

## Proof Check

For `site.service`, identify whether it is a network service, systemd service, system service, user service, or more than one of those.

## Docs Pointers

- Run `man systemd.service` and `man systemctl`.
- Read [systemd service units](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html).
- Read [Server](server.md), [systemd User Services](systemd-user-services.md), [Logging](logging.md), and [Platform Reference](../guides/platform-reference.md).
