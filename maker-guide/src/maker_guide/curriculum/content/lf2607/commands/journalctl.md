# journalctl --user

## Use

Create and start the standalone service from [systemd user services](../concepts/systemd-user-services.md), including its generated test page, before trying these examples.

```bash
journalctl --user -u sample-web.service -f
```

## What It Does

`journalctl --user` reads logs for services managed by your user account.

## Useful Forms

```bash
journalctl --user -u sample-web.service --no-pager -n 50
journalctl --user -u sample-web.service -f
journalctl --user -u sample-web.service --since today
```

Use `-n 50` for recent context. Use `-f` only when you want to watch new lines arrive. While following, make the setup card's curl request in another terminal on the same machine and match its method, path, status, and timestamp to the log. `Ctrl-C` stops the follower, not the service. Stop and disable the sample service when finished, as shown on the setup card.

## What To Look For

- The first error after a restart.
- `ExecStart` failures.
- Caddy startup errors and access-log fields: `request.method`, `request.uri`, `status`, and `ts` in JSON. The sample enables these request logs with `--access-log`.
- Port binding errors.
- Timestamps that show whether you are reading current logs.

## Docs Pointers

- Run `man journalctl`.
- Read [journalctl manual](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html).
- Read [logging](../concepts/logging.md), [service logs](../concepts/service-logs.md), and [systemctl](systemctl.md).
