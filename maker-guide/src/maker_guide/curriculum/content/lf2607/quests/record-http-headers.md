# Record HTTP headers

Quest: record-http-headers

## Mission

Save response headers from your public URL into `~/playground/headers.txt`.

## Commands You Will Use

- `curl -I`
- `>`
- `cat`

## Steps

1. Run `curl -I` against your public URL.
2. Redirect the headers into `~/playground/headers.txt`.
3. Use `cat` to confirm the file starts with an HTTP status line.
4. Ask the guide to check the file.

## Hints

1. `-I` asks for headers only.
2. The first line should begin with `HTTP/`.
3. Use the learner URL shape from the platform reference.

## If Check Fails

Fetch the headers again and make sure `~/playground/headers.txt` contains an `HTTP/` line.

## Related Reading

- [curl -I](../commands/curl-head.md)
- [redirection](../commands/redirect.md)
- [HTTP inspection](../concepts/http-inspection.md)
- [platform reference](../guides/platform-reference.md)
