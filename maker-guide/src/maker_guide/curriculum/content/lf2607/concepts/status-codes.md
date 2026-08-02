# Status Codes

## Core Idea

HTTP status codes summarize what happened to a request.

## Practice Alone

Run a header request and read the first line:

```bash
curl -I https://lf2607.kolamayermakers.org/~username/
```

Useful beginner set:

- `200`: the request succeeded.
- `301` or `302`: the server redirects the client to another URL.
- `404`: the server is reachable, but that path is missing.
- `500`: the backend failed while handling the request.
- `502`: a proxy could not get a valid response from its backend.

For this course, `502` usually means Caddy received the public request but could not reach your user service.

## Done When

You can explain whether failure is missing content, server error, or bad proxying.

## Docs Pointers

- Read [curl -I](../commands/curl-head.md), [HTTP inspection](http-inspection.md), and [reverse proxy](reverse-proxy.md).
