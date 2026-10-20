# HTTP Inspection

## Core Idea

Inspection means reading what the server actually returned, not what you expected.

## Practice Alone

```bash
curl -i --max-time 10 https://example.org/
curl -v --max-time 10 https://example.org/ -o /dev/null
```

The first shows GET headers and body. The second discards the body and exposes DNS, connection, TLS, and response diagnostics. Read the exact error before selecting the next command.

## Done When

Distinguish a DNS error, connection failure, TLS error, and an HTTP response. A `404` means a server answered; a refused connection has no HTTP status. Verbose logs may include private request data—redact them before sharing.

See [curl -v](../commands/curl-verbose.md) and [HTTP status codes](http-status-codes.md).
