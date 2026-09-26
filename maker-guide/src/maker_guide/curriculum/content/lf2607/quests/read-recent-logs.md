# Read Recent Logs

Quest: read-recent-logs

## Mission

Find one fresh web request in your service's journal.

## Request, Then Read

From your classroom SSH shell, request your service homepage. Then read the last five minutes of messages:

```bash
curl -i "https://$USER.lf2607.kolamayermakers.org/"
journalctl --user -u site.service --since "5 minutes ago"
```

Find the request's time, `request.method`, `request.uri`, and `status`. Compare its status with the curl response. Press `q` to leave the journal view.

If the request is missing, check the unit's `--access-log` setting and the error from curl. A request that fails before reaching your Caddy will not appear in its access log. See [Watch service logs](watch-service-logs.md) for a live request experiment.

Run `guide check` when this quest is current to check the recorded commands. Read the result yourself: command history does not show what the server returned.

## Related Reading

- [Journalctl](../commands/journalctl.md)
- [Service logs](../concepts/service-logs.md)
