# Explain status codes

Quest: explain-status-codes

## Mission

Explain `200`, `404`, and `502` in one short answer.

## Commands You Will Use

- `curl -I`

## Steps

1. Read the status-code card.
2. Use `curl -I` on a working page.
3. Think through what missing content and bad backend proxying would return.
4. Answer the guide with all three meanings.

## Hints

1. `200` means success.
2. `404` means missing path.
3. `502` means a proxy could not obtain a usable backend response; an unreachable backend is one possible cause.

## If Check Fails

Explain all three meanings in your own words: `200` is a successful request, `404` means the requested resource was not found, and `502` means a proxy could not obtain a usable backend response. Numbers or a keyword list alone do not satisfy the check.

## Related Reading

- [HTTP status codes](../concepts/http-status-codes.md)
- [curl -I](../commands/curl-head.md)
