# Inspect first URL headers

Quest: inspect-first-url-headers

## Mission

Run `curl -I` against your public `~username` URL and report the status code.

## Commands You Will Use

- `curl -I`

## Steps

1. Build your public URL using your username.
2. Run `curl -I` against that URL.
3. Read the status code from the first line.
4. Answer the guide with the code.

## Hints

1. A healthy page usually returns `200`.
2. `404` means the path was not found.
3. The guide expects the successful public page code.

## If Check Fails

Run `build-website`, try `curl -I` again, and answer with the first status line.

## Related Reading

- [curl -I](../commands/curl-head.md)
- [status-codes](../concepts/status-codes.md)
