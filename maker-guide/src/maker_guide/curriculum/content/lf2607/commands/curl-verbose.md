# curl -v

## Use

```bash
curl -v https://example.org
```

## What It Does

`curl -v` prints connection details, request headers, and response details.

## Practice

Use it when a plain request fails and you need to see where.

## Watch Out

Verbose output mixes diagnostic lines with response data. Read carefully.

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
- `502` from the public service URL: check `systemctl --user status site.service` and the journal.
- Output is too much: redirect stderr to a file with `curl -v URL >/tmp/body 2>/tmp/curl.log`.

## Docs Pointers

- Run `man curl` and search for `-v`.
- Read [everything curl: verbose](https://everything.curl.dev/usingcurl/verbose/).
- Read [curl](curl.md), [curl -I](curl-head.md), [HTTP inspection](../concepts/http-inspection.md), [reverse proxy](../concepts/reverse-proxy.md), and [service logs](../concepts/service-logs.md).
