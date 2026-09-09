# Read HTTP headers

Quest: read-http-headers

## Mission

Run `curl -I` on your personal homepage and report the status line or Server header.

## Commands You Will Use

- `curl -I`

## Steps

1. Run `curl -I "https://lf2607.kolamayermakers.org/~$USER/"`.
2. Read the first status line.
3. Look for a `server` header if one appears.
4. Use `guide answer 'your observed result'` with the status line including its three-digit code, or a nonempty `Server:` header.

The quoted URL expands `$USER` to your account name. You may also substitute your account name directly, with or without matching quotes. Keep the trailing `/` and no subpath for the homepage check.

## Hints

1. `-I` asks for headers only.
2. HTTP responses start with a status line.
3. Include the HTTP version and three-digit status, such as `HTTP/2 200`. The version alone is not a result.

## If Check Fails

Include the three-digit code in the status line, or the value of the `Server:` header. The quest checks your reported answer, not captured HTTP output. A connection failure is not an HTTP status; inspect curl's diagnostic and ask for help if needed.

## Related Reading

- [S6 self-study](../sessions/S06/self-study.md)
- [curl -I](../commands/curl-head.md)
- [http-basics](../concepts/http-basics.md)
