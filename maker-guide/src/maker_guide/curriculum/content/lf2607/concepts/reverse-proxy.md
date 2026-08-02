# Reverse Proxy

## Core Idea

A reverse proxy receives a public request and forwards it to another server or process behind it.

In this course, Caddy is the reverse proxy for the user service URL. Your user-managed service is the backend.

```text
static URL:  https://lf2607.kolamayermakers.org/~username/
service URL: https://username.lf2607.kolamayermakers.org/
```

## Request Path

```text
browser or curl -> Caddy -> your service port -> response back through Caddy
```

The static URL can be served as files from `~/public_html/`. The service URL needs your backend process to be listening on your assigned local port.

## Failure Model

- Caddy reachable, backend missing: proxy-style error such as `502` or connection failure.
- Backend listening on wrong port: Caddy cannot reach it.
- Backend returns an error: Caddy may be working correctly while your service fails.

## Proof Check

Use `curl -v` on the service URL before the service exists, then explain which part is public proxy and which part is missing backend.

## Docs Pointers

- Read [Caddy](../commands/caddy.md), [curl -v](../commands/curl-verbose.md), [HTTP](http.md), [services](service.md), [sockets](sockets.md), and [platform reference](../guides/platform-reference.md).
