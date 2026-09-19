# Reverse Proxy

## Core Idea

A reverse proxy receives a public request and forwards it to another server or process behind it.

A server such as Caddy can serve static files directly on one route and proxy a different route to a backend process. Both routes can use the same files without sharing the backend's lifecycle.

The backend can also be Caddy: the same software, two separate processes. A shared Caddy process handles public HTTPS; a personal `caddy file-server` process serves plain HTTP on loopback. Stopping the personal process does not stop the shared proxy or its direct static-file route.

## Request Path

```text
browser or curl -> proxy -> configured backend port -> response back through proxy
browser or curl -> static file server -> published files
```

The proxied route needs a backend listening on the configured address and port. A direct static-file route does not. Public HTTPS can end at the proxy while the backend receives HTTP over loopback; loopback binding does not make content private if a proxy publishes it.

## Failure Model

- Proxy reachable, backend missing: the public route may return HTTP `502`, while direct loopback access is refused without an HTTP response.
- Backend listening on the wrong port: the proxy cannot reach it at its configured destination.
- Backend returns an error: the proxy may be working correctly while the requested resource fails.
- DNS or TLS failure: the client has not received an HTTP status; do not call that `502`.
- Static route still works: its file delivery does not prove the separate backend is running.

## Proof Check

Run the self-contained [manual server example](../commands/caddy.md), observe its response, stop it with `Ctrl-C`, and repeat the direct request. That demonstrates backend availability only; it does not configure or test a public proxy. Explain why a proxy aimed at that now-closed port could return `502`, while an independent static-file route could still work. On an existing deployment, compare direct and public observations before diagnosing the cause; never change shared routing or stop another user's process for this exercise. Do not use `caddy stop` or `caddy reload`: they might target the shared proxy, not this file server.

## Docs Pointers

- Read [Caddy](../commands/caddy.md), [curl -v](../commands/curl-verbose.md), [HTTP](http.md), [services](service.md), and [sockets](sockets.md).
