# curl

## Use

```bash
curl https://example.org
```

## What It Does

`curl` fetches data from a URL and prints the response body.

## Practice

Use a small page before trying large downloads:

```bash
curl -I https://example.org
curl -i https://example.org
```

`-I` sends `HEAD`, requesting headers without a body. Lowercase `-i` keeps `GET` and prints headers along with the body. `-L` follows redirects; without it you see the original response.

## Capture A Status

```bash
status=$(curl -sS -I --max-time 10 -o /dev/null -w '%{http_code}' https://example.org)
printf 'HTTP status: %s\n' "$status"
```

`-sS` hides the progress meter but keeps errors. `--max-time 10` bounds the request. `-o /dev/null` discards headers; `-w` prints the HTTP code. Bash's `$()` captures stdout, not stderr.

## Watch Out

Without `-I`, curl downloads the body, not just headers.

HTTP status and command exit status are different: receiving a `404` normally still gives curl exit status `0`. `-f` makes HTTP errors fail the command. Without a response, curl commonly prints `000`, which is not an HTTP status code. Test the command's exit status before interpreting a captured code; see [Conditionals](../concepts/conditionals.md).

Keep TLS certificate checks enabled. `-k` hides trust problems rather than repairing them. A `HEAD` result need not match `GET` on every server, and `200` alone does not validate page contents.

## Docs Pointers

- Run `man curl`.
- Read [curl -I](curl-head.md), [curl -v](curl-verbose.md), [HTTP](../concepts/http.md), [client](../concepts/client.md), and [server](../concepts/server.md).
