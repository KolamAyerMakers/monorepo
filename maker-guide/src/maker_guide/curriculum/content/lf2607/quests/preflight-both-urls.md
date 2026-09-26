# Preflight both URLs

Quest: preflight-both-urls

## Mission

Reuse the static checker, request both the static homepage and the service hostname with `curl -I`, and inspect the actual service state.

## Steps

`systemctl show` prints service properties. `ActiveState` is the overall state and `SubState` gives more detail; `-p` selects each property. In your SSH shell:

```bash
bash ~/scripts/site-check.sh "" maker-report.html
curl -I --max-time 10 "https://lf2607.kolamayermakers.org/~$USER/"
curl -I --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
systemctl --user show site.service -p ActiveState -p SubState
curl -i --max-time 10 "http://127.0.0.1:$((10000 + $(id -u)))/"
```

The script checks the static homepage and report. The two public curl commands check different routes: shared Caddy serves the static URL directly, while the service hostname forwards to your Caddy.

Read each HTTP status and the service state. A successful curl command can still report `404` or `502`.

Replace `your-handle` and open the [static homepage](https://lf2607.kolamayermakers.org/~your-handle/), [report](https://lf2607.kolamayermakers.org/~your-handle/maker-report.html), and [service homepage](https://your-handle.lf2607.kolamayermakers.org/) in your laptop browser. Inspect the content as well as reachability.

Run `guide check` when this quest is current. Investigate any failed responses before moving on.

## If Check Fails

Repeat both distinct `curl -I` requests and the status command. A static homepage `404` points to build/output trouble; use the unchanged checker for report-specific repair advice. For service trouble, collect:

```bash
curl -i --max-time 10 "http://127.0.0.1:$((10000 + $(id -u)))/"
journalctl --user -u site.service --since "5 minutes ago"
```

Press `q` to leave the journal. A local refusal means no connection was established; a public `502` means the proxy could not get a usable backend response. Use the [troubleshooting guide](../sessions/S08/self-study.md#troubleshooting), then ask for help with the results if still stuck. Do not change shared routing or bypass TLS checks.

## Related Reading

- [curl -I](../commands/curl-head.md)
- [systemctl](../commands/systemctl.md)
- [platform reference](../guides/platform-reference.md)
- [reverse proxy](../concepts/reverse-proxy.md)
