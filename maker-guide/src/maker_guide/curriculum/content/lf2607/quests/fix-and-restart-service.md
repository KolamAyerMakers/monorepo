# Fix and restart service

Quest: fix-and-restart-service

## Mission

Fix `site.service`, restart it, and verify both site URLs with `curl`.

## Commands You Will Use

- `systemctl --user`
- `curl`
- `journalctl --user`

## Steps

1. Restore the valid `site.service` file.
2. Run `systemctl --user daemon-reload`.
3. Run `systemctl --user restart site.service`.
4. Run `curl` against both public URLs.
5. Ask the guide to check command history.

## Hints

1. Restart after changing a unit or served files.
2. Use logs if restart fails.
3. The guide needs to see restart and curl.

## If Check Fails

Run `systemctl --user status site.service`, fix the error, restart, and curl again.

## Related Reading

- [systemctl](../commands/systemctl.md)
- [systemd-user-services](../concepts/systemd-user-services.md)
