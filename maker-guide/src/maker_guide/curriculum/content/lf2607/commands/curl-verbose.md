# curl -v

## Use

```bash
curl -v --max-time 10 https://example.org
```

## What It Does

`curl -v` prints connection details, request headers, and response details.

## Practice

Use it when a plain request fails and you need to see where.

## Watch Out

Diagnostics go to stderr; the body goes to stdout. Verbose logs can contain credentials and private request data. Redact them before sharing.

## What To Look For

- DNS resolution lines.
- Connection attempt and connected address.
- TLS handshake messages for HTTPS.
- Request lines beginning with `>`.
- Response lines beginning with `<`.
- HTTP status code.

## Recovery

- No DNS answer: use `host NAME`.
- Connection refused: the service is not listening on the target address and port.
- `502`: the proxy answered but could not get a valid backend response. If you manage that backend, inspect its status and logs; otherwise report the exact result to its owner.
- Output is too much: in a fresh temporary directory, capture stdout and stderr separately:

```bash
work=$(mktemp -d)
curl -v --max-time 10 https://example.org >"$work/body.html" 2>"$work/curl.log"
less "$work/curl.log"
```

## Docs Pointers

- Run `man curl` and search for `-v`.
- Read [everything curl: verbose](https://everything.curl.dev/usingcurl/verbose/).
- Read [curl](curl.md), [curl -I](curl-head.md), [HTTP inspection](../concepts/http-inspection.md), [reverse proxy](../concepts/reverse-proxy.md), and [service logs](../concepts/service-logs.md).
