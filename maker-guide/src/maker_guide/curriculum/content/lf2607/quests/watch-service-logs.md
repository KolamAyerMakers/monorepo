# Watch Service Logs

Quest: watch-service-logs

## Mission

Match real page requests to your service journal and distinguish a missing page from a failed process. Use two SSH shells; tmux is optional.

## Follow And Request

Start with your own working [user service](enable-site-service.md). In one SSH shell:

```bash
journalctl --user -u site.service -f
```

In the other, with `$USER` matching your classroom login:

```bash
curl -i --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
curl -i --max-time 10 "https://$USER.lf2607.kolamayermakers.org/missing-log-page.html"
```

Choose a different missing path if that file exists. Ask a peer to open your [service homepage](https://your-handle.lf2607.kolamayermakers.org/), replacing `your-handle`, and an agreed missing path from their browser too.

The unit's `--access-log` enables structured request logs. Find the new entries by time (`ts` in JSON), `request.method`, `request.uri`, and `status`; formatting can differ from the foreground terminal. Do not assume the most recent line belongs to your peer: browsers may make extra requests or reuse a cached page. Your personal Caddy often logs `request.remote_ip` as `127.0.0.1` because shared Caddy is its direct client, not because the visitor is on the server.

## Stop Following, Not Serving

Press `Ctrl-C` in the follower shell, then:

```bash
journalctl --user -u site.service --no-pager -n 20
```

Reload the homepage. It should still work: stopping `journalctl` does not stop your Caddy. A missing path's `404` is an HTTP response from the running backend, not proof of a failed unit. With browsing disabled, a missing index can also produce `404` at `/`.

## If No Request Appears

Confirm the request used the service hostname, not shared Caddy's direct static route. Check the actual public error and `systemctl --user status site.service --no-pager`, and confirm the unit includes `--access-log`. A public DNS failure or proxy `502` may never reach your personal Caddy. Confirm with local curl using your assigned port, then ask staff about unresolved routing; do not change shared services or TLS verification.

## Keep A Useful Observation

Add a brief explanation to existing `~/src/pages/setup.md`: which request you recognized, what its status meant, and why stopping the follower left the page available. Summarize rather than publishing private logs. Ask before naming a peer. Build and [preserve only the intended source change](../sessions/S07/self-study.md#6-preserve-source-now).

Success is recognizing a visitor's request and explaining the result, not producing a particular command history.

## Related Reading

- [Journalctl](../commands/journalctl.md)
- [Service logs](../concepts/service-logs.md)
- [S8 request experiment](../sessions/S08/self-study.md#5-follow-real-requests)
