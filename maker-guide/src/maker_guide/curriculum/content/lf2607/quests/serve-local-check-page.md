# Serve A Local Check Page

Quest: serve-local-check-page

## Mission

Run your own foreground backend and fetch its page locally with curl. Then try the public service hostname and watch for visitors. Two SSH connections are enough; no extra tool or helper script is required.

## Start In One SSH Shell

Use your own classroom account and existing published site in `~/public_html`. If the site needs publishing, run `build-website` and resolve any error first. Do not create another source tree.

If an unknown process already occupies your port, ask staff rather than killing it.

```bash
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
```

This course assigns port `10000 + uid`. If the number exceeds `65535`, stop and ask staff. Otherwise:

```bash
caddy file-server --listen ":$PORT" --root "$HOME/public_html" --access-log
```

Keep this terminal visible. Your personal Caddy listens for plain HTTP on all interfaces; the classroom firewall blocks new direct external connections to its port. Shared Caddy handles public HTTPS and proxies to `127.0.0.1` at that port. Same software, two processes. Do not add `--domain`. No configuration file is needed, and `file-server` disables the admin API. The explicit root prevents accidental serving of your shell's current directory. Caddy follows symlinks, so `--root` is not a filesystem sandbox: keep credentials and links to private files out of the published tree, which remains public through the shared proxy.

## Request In Another SSH Shell

```bash
PORT="$((10000 + $(id -u)))"
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
```

Read the status and page body. Now open your [service homepage](https://your-handle.lf2607.kolamayermakers.org/) in your laptop browser, replacing `your-handle`, and ask a peer to visit. Ask them to request an agreed missing path too. `--access-log` records structured fields: match `request.uri`, `request.method`, `status`, and time (`ts` in JSON) to the first terminal's log. Formatting can differ between terminal and journal output. `request.remote_ip` may show the shared proxy's `127.0.0.1` address rather than the visitor's address.

If public access fails, keep the actual error and compare it with the successful local request. DNS and TLS failures have no HTTP status; do not invent a public response or visitor log.

## Leave It Working

After any optional extension below, press `Ctrl-C` in your server terminal when finished. The manual process can end; your static site remains available.

Do not use `caddy stop` or `caddy reload`: these admin-API commands might target the shared Caddy instead of your file server. Do not edit shared configuration.

Success means local curl received your recognizable page from your own running backend and you can identify the matching request log. Public and peer attempts provide additional observations; publishing, notes, and Git are not required for this practical result.

## Optional Publishing Extension

For extra practice while Caddy runs, edit an existing page source, run `build-website`, and reload after success without restarting Caddy. The explicit root path lets new requests find the newly replaced `public_html` tree.

If you want published operating notes, follow [Create a setup page](create-setup-page.md) first when `~/src/pages/setup.md` is absent. Preserve existing files and links, add useful observations, then build. You can [preserve intended source changes in Git](../sessions/S07/self-study.md#6-preserve-source-now). No credentials or raw private logs.

## If It Does Not Work

- `Address already in use`: find your own previous manual server or unit. Do not change the assigned port or kill another learner's process.
- Local refusal: confirm the server is running and both SSH shells use the same account, machine, and computed port.
- HTTP `404`: inspect the published path and build result. With browsing disabled, a missing `index.html` makes `/` return `404` even if the process is healthy; never remove `--root` or enable browsing to hide missing output.
- Local access works but public access fails: bring the actual public error and local result to staff. Do not use `sudo`, change shared routing, or bypass TLS.

## Related Reading

- [S7 practical route](../sessions/S07/self-study.md)
- [Caddy file-server](../commands/caddy.md)
- [Curl](../commands/curl.md)
- [Reverse proxy](../concepts/reverse-proxy.md)
