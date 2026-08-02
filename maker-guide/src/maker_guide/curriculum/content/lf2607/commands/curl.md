# curl

## Use

```bash
curl https://example.org
```

## What It Does

`curl` fetches data from a URL and prints the response body.

## Practice

Use it for small text endpoints before using it on large pages.

## Watch Out

Without `-I`, curl downloads the body, not just headers.

## Docs Pointers

- Run `man curl`.
- Read [curl -I](curl-head.md), [curl -v](curl-verbose.md), [HTTP](../concepts/http.md), [client](../concepts/client.md), and [server](../concepts/server.md).
