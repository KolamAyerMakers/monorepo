# Explain a 502

Quest: explain-502

## Mission

Explain why a reverse proxy returns 502 when the backend service is missing.

## Commands You Will Use

- `curl -v`

## Steps

1. Run `curl -v` against a URL that depends on a backend service.
2. Read the connection details.
3. Explain the proxy and backend service roles.
4. Answer the guide in your own words.

## Hints

1. The proxy receives the public request first.
2. The backend service must be listening behind it.
3. A missing backend can produce a 502.

## If Check Fails

Answer again and mention the backend service explicitly.

## Related Reading

- [curl -v](../commands/curl-verbose.md)
- [reverse proxy](../concepts/reverse-proxy.md)
- [status codes](../concepts/status-codes.md)
