# Break and read the error

Quest: break-and-read-error

## Mission

Temporarily break `site.service`, read the journal error, then restore and verify the service.

## Commands You Will Use

- `systemctl --user`
- `journalctl --user`
- `micro`
- `curl`

## Steps

1. Copy the working unit first: `cp ~/.config/systemd/user/site.service ~/site.service.backup`.
2. Make one safe typo in `site.service`, such as changing `/usr/bin/python3` to `/no/such/python`.
3. Run `systemctl --user daemon-reload`.
4. Restart the service and let it fail.
5. Read `journalctl --user -u site.service --no-pager -n 50`.
6. Restore the backup with `cp ~/site.service.backup ~/.config/systemd/user/site.service`.
7. Run `systemctl --user daemon-reload` and `systemctl --user restart site.service`.
8. Verify with `systemctl --user status site.service` and local `curl`.
9. Answer the guide with what the error said.

## Hints

1. Break only something you know how to restore.
2. Logs are evidence, not decoration.
3. Use the word `error` in your answer, but leave the service working afterward.

## If Check Fails

Restore `~/site.service.backup`, run `systemctl --user daemon-reload`, restart `site.service`, verify local `curl`, then read the journal again and answer with the specific failure message.

## Related Reading

- [journalctl](../commands/journalctl.md)
- [systemctl](../commands/systemctl.md)
- [curl](../commands/curl.md)
- [service-logs](../concepts/service-logs.md)
