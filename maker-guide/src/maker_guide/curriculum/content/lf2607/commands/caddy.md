# caddy

## Use

```bash
caddy validate --config Caddyfile
```

## What It Does

Caddy is the public web server in front of learner sites. It receives HTTPS requests, serves static files for the first URL, and routes the second URL to your user-managed service.

## Practice

In this course, read Caddy behavior and error messages. Do not edit server config.

Useful inspection commands:

```bash
curl -I https://lf2607.kolamayermakers.org/~username/
curl -v https://lf2607.kolamayermakers.org/~username/
curl -I https://username.lf2607.kolamayermakers.org/
```

If the first URL works and the second URL returns a proxy-style failure, Caddy is reachable but your backend service is probably missing or broken.

## Watch Out

Most Caddy administration is not a learner permission on the shared server.

Do not confuse Caddy with your service. Caddy is the front door; your service is the backend for the second URL.

## Docs Pointers

- Read [Caddy documentation](https://caddyserver.com/docs/).
- Read [reverse proxy](../concepts/reverse-proxy.md), [HTTP](../concepts/http.md), [services](../concepts/service.md), and [curl -v](curl-verbose.md).
