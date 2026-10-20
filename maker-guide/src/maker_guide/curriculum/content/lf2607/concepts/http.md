# HTTP

## Core Idea

HTTP is a request-response protocol: a client asks for a resource, and a server returns a status, headers, and often a body. A response error such as `404` is different from failing to establish a connection.

## Commands To Try

```bash
curl -I --max-time 10 https://example.org/
curl -i --max-time 10 https://example.org/
curl -v --max-time 10 https://example.org/
```

`-I` sends HEAD and shows headers without a body. Lowercase `-i` sends GET and includes headers with the body. `-v` adds connection diagnostics on stderr. `-L` follows redirects when you want the destination rather than only the original response.

## Response Shape

```text
HTTP/1.1 200 OK
server: Caddy
content-type: text/html; charset=utf-8

<html>...</html>
```

- Status line: whether the request succeeded or failed.
- Headers: metadata about the response.
- Blank line: separates headers from the body.
- Body: the resource content, if there is one.

This is an illustrative HTTP/1.1 response, not guaranteed output from the URL above. HTTP/2 and HTTP/3 encode messages differently on the wire, though curl displays readable headers for them too.

## Status Codes To Know

| Code | Meaning |
|---|---|
| `200` | OK. The resource was returned. |
| `301` or `302` | Redirect. Try `curl -L`. |
| `404` | Not found. The server could not find that path. |
| `500` | Server error. The server failed while handling the request. |
| `502` | Bad gateway. A proxy could not reach or use its backend. |

## Methods

GET requests the representation, such as an HTML page. HEAD asks for its headers without the body. Some servers handle these differently, so a HEAD check is not a substitute for inspecting the actual GET result.

## HTTP Versus HTTPS

HTTP is the protocol. HTTPS is HTTP carried inside TLS encryption. HTTPS protects the request and response in transit and lets the client verify the server certificate.

## Common Failures

- `404`: inspect the URL path and the intended file/routing; the server did respond.
- `502`: a gateway could not obtain a valid upstream response. If you manage the backend, inspect its process and logs; otherwise report the result to its owner.
- Redirect loop or surprise redirect: inspect with `curl -L -I` and read each `location` header.
- Certificate error: read the hostname and certificate message; do not bypass it blindly.

## Proof Check

Run the first two commands above. Identify the status, a header, and where the GET body begins. Receiving an HTTP error normally still gives curl exit status `0`; `-f` changes that. No response may produce curl's `000` placeholder, which is not an HTTP status.

## Docs Pointers

- Run `man curl`.
- Read [MDN: Overview of HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview).
- Read [MDN: HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status).
- Read [everything curl](https://everything.curl.dev/).
