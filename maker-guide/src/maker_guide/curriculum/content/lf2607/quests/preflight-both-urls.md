# Preflight both URLs

Quest: preflight-both-urls

## Mission

Check both public URLs with `curl -I` and inspect service status.

## Commands You Will Use

- `curl -I`
- `systemctl --user`

## Steps

1. Run `curl -I "https://lf2607.kolamayermakers.org/~$(whoami)/"`.
2. Run `curl -I "https://$(whoami).lf2607.kolamayermakers.org/"`.
3. Run `systemctl --user status site.service`.
4. Ask the guide to check the command history.

## Hints

1. Header checks are enough for this preflight.
2. Check the service after checking URLs.
3. Use failures as a debugging list. Bring unresolved failures to the polish session.

## If Check Fails

Run both `curl -I` checks and the service status command again. A static URL `404` points to build/output trouble. A service URL `502` points to service, port, or proxy trouble. A DNS failure needs the platform-reference DNS checks.

## Related Reading

- [curl -I](../commands/curl-head.md)
- [systemctl](../commands/systemctl.md)
- [platform reference](../guides/platform-reference.md)
- [reverse proxy](../concepts/reverse-proxy.md)
