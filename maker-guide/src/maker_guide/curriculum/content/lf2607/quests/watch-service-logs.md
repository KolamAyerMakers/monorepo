# Watch Service Logs

Quest: watch-service-logs

## Mission

Match page requests to your service journal. Distinguish a missing page from a failed process.

## Follow And Request

Start with your working [user service](enable-site-service.md). `journalctl` reads its journal; `-f` follows new messages:

```bash
journalctl --user -u site.service -f
```

Ask a peer to visit your [service homepage](https://your-handle.lf2607.kolamayermakers.org/), replacing `your-handle`, then `/missing.html` on that site. If working alone, make the requests from a second SSH shell:

```bash
curl -i "https://$USER.lf2607.kolamayermakers.org/"
curl -i "https://$USER.lf2607.kolamayermakers.org/missing.html"
```

Choose another missing path if that file exists. Find each request's time (`ts` in JSON), `request.method`, `request.uri`, and `status`. Browsers can make extra requests, so match the path and time rather than assuming the last entry is yours.

## Stop Following, Not Serving

Press `Ctrl-C`, then reload the homepage. Caddy should still respond: you stopped `journalctl`, not the server. Read the recent entries again:

```bash
journalctl --user -u site.service --since "5 minutes ago"
```

Press `q` to leave. A `404` for the missing page means the server answered, not that it stopped.

## Explain One Request

Report its method, path, status, and time, then explain why ending the log follower left the site available. Use `guide answer 'Your observation and explanation'` when this quest is current. Summarize the request rather than publishing private logs; no notes page is required.

If nothing appears, check that you used the service hostname, not the static route, and that the unit includes `--access-log`. A DNS failure or public proxy error may never reach your Caddy. Use the [S8 troubleshooting table](../sessions/S08/self-study.md#troubleshooting) rather than changing shared services.

## Related Reading

- [Journalctl](../commands/journalctl.md)
- [Service logs](../concepts/service-logs.md)
- [S8 request experiment](../sessions/S08/self-study.md#5-follow-real-requests)
