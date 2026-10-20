# Logging

## Core Idea

Logging is the practice of recording events, warnings, errors, and context so a future human can understand what happened.

## Logs Versus Output

Output is what a command prints to the caller. Logs are records kept for diagnosis; systemd commonly captures a service's stdout and stderr in the journal. A proxy's short `502` response may have a more useful explanation in its own logs or the backend's logs.

## Commands to Try

First create and start the [sample web service](systemd-user-services.md), which supplies its own page and unit:

```bash
journalctl --user -u sample-web.service --no-pager -n 50
journalctl --user -u sample-web.service -f
systemctl --user status sample-web.service
```

Use `status` for the current summary and `journalctl` for the detailed event history.

## What Good Logs Tell You

- When the event happened.
- Which service or process emitted it.
- What operation was attempted.
- What failed or succeeded.
- Enough context to choose the next diagnostic command.

## How To Read Logs

1. Start at the newest relevant failure.
2. Read upward until you find the first cause, not just the final symptom.
3. Compare timestamps with your attempted restart or request.
4. Fix one cause at a time.
5. Re-run the same proof command after the fix.

## Common Confusions

- A log line after the failure may be cleanup, not the cause.
- A warning is not always fatal.
- Old logs can distract you; use `--since today` or `-n 50`.
- Time zones matter when comparing logs with external events.

## Proof Check

Restart your demo with `systemctl --user restart sample-web.service`, then run `journalctl --user -u sample-web.service --no-pager -n 20`. Identify the timestamp and a message from that restart. Stop and disable the demo as shown on its setup card when finished.

## Docs Pointers

- Run `man journalctl`.
- Read [journalctl manual](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html).
- Read [Service](service.md), [Service Logs](service-logs.md), and [Time Zones](time-zones.md).
