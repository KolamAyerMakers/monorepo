# Read recent logs

Quest: read-recent-logs

## Mission

Read recent `site.service` logs after making a request with `curl`.

## Commands You Will Use

- `journalctl --user`
- `curl`

## Steps

1. Make a request to your service with `curl`.
2. Run `journalctl --user -u site.service`.
3. Look for recent log lines.
4. Ask the guide to check your command history.

## Hints

1. Logs are easier to read after a fresh request.
2. The unit name is `site.service`.
3. Run both commands before asking for a check.

## If Check Fails

Run a `curl` request and then inspect `site.service` with `journalctl --user`.

## Related Reading

- [journalctl](../commands/journalctl.md)
- [curl](../commands/curl.md)
- [service logs](../concepts/service-logs.md)
- [logging](../concepts/logging.md)
