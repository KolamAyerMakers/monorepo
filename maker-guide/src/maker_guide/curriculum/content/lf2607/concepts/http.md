# HTTP

## Core Idea

HTTP is a request-response protocol: a client asks for a resource, and a server returns a status line, headers, and usually a body.

## Commands To Try

```bash
curl -I https://lf2607.kolamayermakers.org/~username/
curl -L https://lf2607.kolamayermakers.org/~username/
curl -v https://lf2607.kolamayermakers.org/~username/
```

`curl -I` shows headers. Plain `curl` shows the body. `curl -v` shows the client-server conversation.

## Response Shape

```text
HTTP/2 200
server: Caddy
content-type: text/html; charset=utf-8

<html>...</html>
```

- Status line: whether the request succeeded or failed.
- Headers: metadata about the response.
- Blank line: separates headers from the body.
- Body: the resource content, if there is one.

## Status Codes To Know

| Code | Meaning |
|---|---|
| `200` | OK. The resource was returned. |
| `301` or `302` | Redirect. Try `curl -L`. |
| `404` | Not found. The server could not find that path. |
| `500` | Server error. The server failed while handling the request. |
| `502` | Bad gateway. A proxy could not reach or use its backend. |

## Methods

This course mostly uses `GET` and header-only inspection. `curl -I` sends a `HEAD` request, which asks for headers without the body.

## HTTP Versus HTTPS

HTTP is the protocol. HTTPS is HTTP carried inside TLS encryption. HTTPS protects the request and response in transit and lets the client verify the server certificate.

## Common Failures

- `404`: rebuild the site or check the path and filename.
- `502`: check the backend service with `systemctl --user status site.service`.
- Redirect loop or surprise redirect: inspect with `curl -L -I` and read each `location` header.
- Certificate error: read the hostname and certificate message; do not bypass it blindly.

## Proof Check

Fetch your static site with `curl -I`. Identify the status code, server header, and content type.

## Docs Pointers

- Run `man curl`.
- Read [MDN: Overview of HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview).
- Read [MDN: HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status).
- Read [everything curl](https://everything.curl.dev/).
