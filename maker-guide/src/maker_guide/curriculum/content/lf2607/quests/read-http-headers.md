# Read HTTP headers

Quest: read-http-headers

## Mission

Run `curl -I https://github.com` and report the status line or Server header.

## Commands You Will Use

- `curl -I`

## Steps

1. Run `curl -I https://github.com`.
2. Read the first status line.
3. Look for a `server` header if one appears.
4. Answer the guide with a status line or header.

## Hints

1. `-I` asks for headers only.
2. HTTP responses start with a status line.
3. Include the word `HTTP` if you report the status line.

## If Check Fails

Run the curl command again and answer with one exact header or the status line.

## Related Reading

- [curl -I](../commands/curl-head.md)
- [http-basics](../concepts/http-basics.md)
