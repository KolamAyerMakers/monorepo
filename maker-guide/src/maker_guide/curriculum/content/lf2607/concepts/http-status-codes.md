# HTTP Status Codes

## Core Idea

HTTP status codes summarize what happened to a request.

## Practice Alone

Run a header request and read the first line:

```bash
curl -I https://example.org
```

Read the first digit first:

- `2xx`: success.
- `3xx`: redirection or further action, such as using a cached representation.
- `4xx`: the server cannot fulfil this request, for example a missing path or denied access.
- `5xx`: the server failed while handling the request.

Common examples:

- `200`: the request succeeded.
- `301` or `302`: the server redirects the client to another URL.
- `304`: the client can use its cached representation; not a move to another URL.
- `403`: access is forbidden.
- `404`: the server is reachable, but that path is missing.
- `500`: the backend failed while handling the request.
- `502`: a proxy could not get a valid response from its backend.

`502` points to a gateway/upstream problem, not automatically to the client or the requested filename. Inspect the actual service configuration and logs before deciding on a repair.

An HTTP error response can still mean curl completed successfully. `000` is curl's no-response placeholder, not an HTTP status code.

## Done When

You can explain whether failure is missing content, server error, or bad proxying.

## Docs Pointers

- Read [curl -I](../commands/curl-head.md), [HTTP inspection](http-inspection.md), and [reverse proxy](reverse-proxy.md).
