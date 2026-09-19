# Explain A 502

Quest: explain-502

## Mission

Use your own backend observations to explain why the service route can fail while the static page still works. A `502` is a proxy response, not a synonym for every network error.

## Predict And Observe

Reuse your [S7 stop-and-recover observations](../sessions/S07/self-study.md#7-predict-stop-and-recover), or repeat that brief experiment with your own manual server. Stop only your known foreground server with `Ctrl-C` in its terminal, and restore it afterward. Never stop an unknown process or another learner's service.

In your classroom SSH shell:

```bash
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
```

Use only the assigned course port. If it exceeds `65535`, ask staff before proceeding. While your backend is stopped:

```bash
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
curl -v --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
curl -I --max-time 10 "https://lf2607.kolamayermakers.org/~$USER/"
```

With routing working, expect local connection refusal, public service HTTP `502`, and a working static page. Record actual results. Do not disable TLS verification or change shared routing to force the prediction.

## Explain The Difference

- Local refusal means the connection was not accepted at that endpoint; there is no HTTP status to read.
- A public `502 Bad Gateway` means the proxy could not obtain a usable upstream response. A stopped backend is one possible cause, not the only one.
- The paired local refusal and controlled stop support the missing-listener diagnosis in this experiment. A `502` alone does not prove the process is stopped.
- Shared Caddy's static delivery bypasses your personal Caddy backend and still reads the published files. The shared process handles public HTTPS and forwards to your backend over loopback HTTP. Your backend listens on all interfaces; the classroom firewall blocks new direct external connections to its port.
- A `404` means an HTTP server answered but did not find that path. DNS failure, TLS failure, and timeout are different failures, not HTTP `502`.

## Restore And Keep

For a manual backend, relaunch in its original terminal:

```bash
PORT="$((10000 + $(id -u)))"
caddy file-server --listen ":$PORT" --root "$HOME/public_html" --access-log
```

Relaunch your known manual server if you stopped it; do not launch a competing server on an occupied port. Repeat local curl and try the public service page in the laptop browser. Ask a peer to try too. Explain which component returned the earlier error, or why DNS or TLS failed before any HTTP response. Report unresolved public access separately from local recovery.

Do not leave a deliberately stopped managed service behind. Published notes are optional: if you want them and `~/src/pages/setup.md` is absent, follow [Create a setup page](create-setup-page.md) before building. Preserve existing content when adding the diagnosis; you may build and [preserve only the intended source change](../sessions/S07/self-study.md#6-preserve-source-now). No credentials or private logs.

## Related Reading

- [Diagnose the service URL](diagnose-second-url.md)
- [Reverse proxy](../concepts/reverse-proxy.md)
- [HTTP status codes](../concepts/http-status-codes.md)
