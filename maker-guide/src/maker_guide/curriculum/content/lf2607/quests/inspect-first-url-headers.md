# Inspect your static URL headers

Quest: inspect-first-url-headers

## Mission

Run `curl -I` against your public `~username` URL and report the status code.

## Commands You Will Use

- `curl -I`

## Steps

1. Build your public URL using your username.
2. Run `curl -I --max-time 10` against that URL.
3. Read the actual three-digit status code from the HTTP status line, if one was received.
4. Answer the guide with that observed code, including a non-`200` result. Do not substitute an expected success code.

## Hints

1. A healthy page usually returns `200`.
2. `404` means the path was not found.
3. Any actual three-digit HTTP status is valid evidence here, not only `200`. DNS or TLS failures before a response have no HTTP status; report the error rather than inventing a code.

## If Check Fails

Compare your answer with the actual status line and retry if needed. For `404`, inspect the URL, source, and generated path; rebuild only if output is missing or stale. For DNS or TLS errors, keep the exact error and ask staff; a rebuild cannot repair those failures. Do not disable certificate verification. Report other HTTP errors as observed rather than rebuilding for every failure.

## Related Reading

- [curl -I](../commands/curl-head.md)
- [HTTP status codes](../concepts/http-status-codes.md)
