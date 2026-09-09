# Preflight both URLs

Quest: preflight-both-urls

## Mission

Reuse the static checker, request both the static homepage and the service hostname with `curl -I`, and inspect the actual service state.

## Commands You Will Use

- `curl -I`
- `systemctl --user`

## Steps

On the classroom server, confirm `$USER` matches your course login, then run:

```bash
bash ~/scripts/site-check.sh
curl -I "https://lf2607.kolamayermakers.org/~$USER/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
systemctl --user show site.service -p ActiveState -p SubState
```

Keep `~/scripts/site-check.sh` unchanged: it checks the static homepage and report. It does not check the service hostname. The explicit curl commands request two different hostnames; requesting the static URL twice does not cover the service.

Read each response's HTTP status line and the unit's `ActiveState` and `SubState`. `show` reports these properties without treating an inactive or failed state as a failed query. Record that state honestly instead of assuming success because a command ran. Curl can exit `0` after `404` or `502`.

Replace `your-handle` and open the [static homepage](https://lf2607.kolamayermakers.org/~your-handle/), [report](https://lf2607.kolamayermakers.org/~your-handle/maker-report.html), and [service homepage](https://your-handle.lf2607.kolamayermakers.org/) in your laptop browser. Inspect the content as well as reachability.

Run `guide check` for the two distinct curl observations and the service-status command. The guide checks recorded commands, not independent proof of HTTP 200 or browser access.

## Hints

1. Local curl tests your process directly; public-hostname curl from the server tests its proxy route and may use local host mappings. Neither proves outside access.
2. Your laptop browser adds evidence from one outside network, not every visitor's network. A header-only response cannot prove the page content is correct.
3. Use failures as a debugging list. Bring unresolved observations to the polish session instead of fabricating a working service.

## If Check Fails

Repeat both distinct `curl -I` requests and the status command. A static homepage `404` points to build/output trouble; use the unchanged checker for report-specific repair advice. For service trouble, collect:

```bash
PORT="$((10000 + $(id -u)))"
curl -I "http://127.0.0.1:$PORT/"
journalctl --user -u site.service --no-pager -n 50
```

A service `502` points to the process, assigned port, or proxy route. For name-resolution failure, also run `host "$USER.lf2607.kolamayermakers.org"`. Use [enable-site-service](enable-site-service.md) for unit repair and bring unresolved routing evidence to staff; do not change shared DNS or proxy settings.

## Related Reading

- [curl -I](../commands/curl-head.md)
- [systemctl](../commands/systemctl.md)
- [platform reference](../guides/platform-reference.md)
- [reverse proxy](../concepts/reverse-proxy.md)
