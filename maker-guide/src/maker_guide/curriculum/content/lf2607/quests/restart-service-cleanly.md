# Restart service cleanly

Quest: restart-service-cleanly

## Mission

Restart `site.service` and verify the local endpoint with `curl`.

## Commands You Will Use

- `systemctl --user`
- `curl`

## Steps

1. Run `systemctl --user restart site.service`.
2. Fetch the local endpoint with `curl`.
3. Read the response.
4. Ask the guide to check your command history.

## Hints

1. Restart first, verify second.
2. Use the local port for a direct check.
3. Do not trust a restart without a request afterward.

## If Check Fails

Run the exact restart command and then a `curl` request.

## Related Reading

- [systemctl](../commands/systemctl.md)
- [curl](../commands/curl.md)
- [systemd user services](../concepts/systemd-user-services.md)
- [manual web service](../concepts/manual-web-service.md)
