# Diagnose the second URL

Quest: diagnose-second-url

## Mission

Run `curl -v` against your second URL and explain the missing-service failure mode.

## Commands You Will Use

- `curl -v`

## Steps

1. Run `curl -v` against your second URL.
2. Read the status and verbose connection output.
3. Remember that no user-managed service has been created yet.
4. Answer the guide with the cause.

## Hints

1. The second URL needs a backend process.
2. Before your personal service exists, nothing is listening behind that URL.
3. Use the words `service` and `listening` in your answer.

## If Check Fails

Answer again with a sentence explaining that no service is listening behind the second URL yet.

## Related Reading

- [curl -v](../commands/curl-verbose.md)
- [reverse proxy](../concepts/reverse-proxy.md)
