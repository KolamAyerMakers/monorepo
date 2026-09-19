# Diagnose The Service URL

Quest: diagnose-second-url

## Mission

Find where the service URL fails, then confirm the effect of starting or recovering your backend. A manual server can serve this route too; check what the requests show instead of assuming.

## Compare The Routes

In your own SSH account on the classroom server, confirm `$USER` matches `whoami`, then:

```bash
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
```

If the course formula `10000 + uid` exceeds `65535`, ask staff instead of selecting another port. Otherwise:

```bash
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
curl -v --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
curl -I --max-time 10 "https://lf2607.kolamayermakers.org/~$USER/"
```

The service URL is the hostname route, not another static page path. Sketch the two routes:

```text
Service hostname -> shared Caddy (HTTPS) -> personal Caddy (loopback HTTP) -> public_html
Static /~username/ -> shared Caddy (HTTPS) -> public_html
```

These are two Caddy processes using the same software, not one process with two names. Only the service route depends on your personal process.

## Diagnose What You Observed

| Observation | What it tells you |
| --- | --- |
| Local refusal and public `502` | Consistent with no listener at the assigned endpoint and a working public proxy route |
| Local page works, public `502` | Backend responds locally; compare the assigned port, then ask staff about proxy routing |
| Public DNS or TLS error | Failure before an HTTP response, not HTTP `502` |
| HTTP `404` | An HTTP server answered but could not find the requested resource |
| Both routes show the page | The backend is already serving; do not invent a missing-service failure |

`curl -v` marks connection/TLS details with `*`, request headers with `>`, and response headers with `<`. A timeout is a different observation from connection refusal. Public `502` alone does not prove a stopped process.

If no backend is running, follow [Serve a local check page](serve-local-check-page.md). Never kill an unknown process, use `sudo`, change shared routing, or disable certificate verification.

## Explain What Happened

After recovery, request locally and try the [service homepage](https://your-handle.lf2607.kolamayermakers.org/) from your laptop, replacing `your-handle`. Ask a peer to try too. Explain which observation located the failure, what changed, and what remains unresolved. If access already worked, say so; if DNS or TLS fails, explain that no HTTP response was received.

Record actual results, not an expected answer or a command list. Published notes are optional: extend `~/src/pages/setup.md` without replacing its content, then build and [preserve the intended source change](../sessions/S07/self-study.md#6-preserve-source-now). No credentials or private logs.

## Related Reading

- [Curl verbose output](../commands/curl-verbose.md)
- [Reverse proxy](../concepts/reverse-proxy.md)
