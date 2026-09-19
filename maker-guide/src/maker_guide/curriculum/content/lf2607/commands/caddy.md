# caddy

## Use

Use a new or confirmed disposable `~/http-demo` directory; do not overwrite an existing page. Verify `caddy`, `curl`, and `ss` are installed, then inspect the candidate port with `ss -H -ltn 'sport = :8000'`. If a listener appears, choose another unused unprivileged port and use it consistently below. Never kill an unknown process to free a practice port.

```bash
mkdir -p "$HOME/http-demo"
printf '<h1>Local demo</h1>\n' > "$HOME/http-demo/index.html"
PORT=8000
caddy file-server --listen "127.0.0.1:$PORT" --root "$HOME/http-demo" --access-log
```

## What It Does

This creates a demo page and serves it over plain HTTP on loopback port `8000`. `--root` selects files independently of the shell's current directory, and `--access-log` enables request logs. No configuration file is needed; this example does not request a domain, automatic HTTPS, or directory browsing.

Caddy can also run separately as a shared HTTPS reverse proxy. A personal file server and a shared proxy can be the same software in two processes with different owners, listeners, and lifecycles. Starting this demo does not configure a public proxy.

## Practice

In another shell on the same machine:

```bash
PORT=8000
curl -i --max-time 5 "http://127.0.0.1:$PORT/"
curl -i --max-time 5 "http://127.0.0.1:$PORT/missing-example.html"
```

Confirm `missing-example.html` is absent first, or choose another missing name. Expect `200` with the `Local demo` body for `/` and `404` for the absent file. Match the requests to access-log fields: `request.method`, `request.uri`, `status`, and time (`ts` in JSON). `request.remote_ip` identifies the direct client, which can be a loopback proxy rather than the visitor. Terminal formatting can differ from JSON captured by systemd; read field names, not a fixed column position. Startup messages are not request evidence.

Press `Ctrl-C` in the server terminal to stop it. Repeat curl: with no listener left, it fails to connect without an HTTP status. If it still answers, identify the listener before taking action.

## Watch Out

- Keep the explicit `--root`: omitting it serves the current directory. A failed `cd` must not expose unrelated files.
- A directory without an index file returns `404` with browsing disabled, even when the process is healthy. A missing root or requested file can also yield `404`; fix the intended files rather than broadening the root or enabling browsing.
- Only place public files in the serving directory. Caddy follows symlinks, so `--root` is not a filesystem sandbox.
- Loopback allows only local direct connections, but a local reverse proxy can still publish the content to outside visitors.
- A port can become busy after inspection. If startup reports `address already in use`, inspect again instead of stopping someone else's process. Use the assigned port when adapting this demo to an existing proxy route.
- Stop a foreground server with `Ctrl-C`, or a managed one with its own `systemctl --user stop` command. Do not use `caddy stop` or `caddy reload`: they might target a separate shared Caddy process. Do not alter shared configuration.
- Access logs can contain private request data. Summarize observations rather than publishing raw logs.

## Docs Pointers

- Read [Caddy documentation](https://caddyserver.com/docs/).
- Read [Caddy file-server CLI](https://caddyserver.com/docs/command-line#caddy-file-server).
- Read [reverse proxy](../concepts/reverse-proxy.md), [HTTP](../concepts/http.md), [services](../concepts/service.md), and [curl -v](curl-verbose.md).
