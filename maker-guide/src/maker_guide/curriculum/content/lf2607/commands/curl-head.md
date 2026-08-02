# curl -I

## Use

```bash
curl -I https://github.com
```

## What It Does

`curl -I` asks for HTTP headers without the response body.

## Practice

Read the status line first, then headers such as `server` or `location`.

## Watch Out

Some servers respond differently to header-only requests.

## How To Read Output

```text
HTTP/2 200
server: Caddy
content-type: text/html
```

Read the status line first. `200` means success. `301` or `302` means redirect. `404` means missing path. `502` often means a proxy could not reach a backend service.

## Recovery

- Redirected: retry with `curl -L -I URL`.
- Connection refused: service may not be listening.
- Name resolution failure: test DNS with `host` or `dig`.
- TLS or certificate failure: read the exact certificate error before retrying.

## Docs Pointers

- Run `man curl` and search for `-I`.
- Read [curl man page](https://curl.se/docs/manpage.html).
- Read [MDN HTTP status reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status).
- Read [curl](curl.md), [curl -v](curl-verbose.md), [HTTP](../concepts/http.md), and [status codes](../concepts/status-codes.md).
