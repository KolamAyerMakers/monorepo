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
3. `502` often means a proxy could not reach a backend.

## If Check Fails

Answer again and include all three numbers: `200`, `404`, and `502`.

## Related Reading

- [status-codes](../concepts/status-codes.md)
- [curl -I](../commands/curl-head.md)
