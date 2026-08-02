# journalctl --user

## Use

```bash
journalctl --user -u site.service -f
```

## What It Does

`journalctl --user` reads logs for services managed by your user account.

## Useful Forms

```bash
journalctl --user -u site.service --no-pager -n 50
journalctl --user -u site.service -f
journalctl --user -u site-build.service --since today
```

Use `-n 50` for recent context. Use `-f` only when you want to watch new lines arrive.

## What To Look For

- The first error after a restart.
- `ExecStart` failures.
- Python tracebacks.
- Port binding errors.
- Timestamps that show whether you are reading current logs.

## Docs Pointers

- Run `man journalctl`.
- Read [journalctl manual](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html).
- Read [logging](../concepts/logging.md), [service logs](../concepts/service-logs.md), and [systemctl](systemctl.md).
