# Resolve a hostname

Quest: resolve-hostname

## Mission

Run `host lf2607.kolamayermakers.org` and report one address or answer line.

## Commands You Will Use

- `host`

## Steps

1. Run `host lf2607.kolamayermakers.org`.
2. Read the answer lines.
3. Use `guide answer 'your observed result'` with one returned IP address or a complete address or alias answer line.

## Hints

1. DNS translates names into records.
2. `host` may show more than one answer.
3. An address line includes the hostname, `has address` or `has IPv6 address`, and the returned IP. An alias line includes the hostname, `is an alias for`, and the target hostname.

## If Check Fails

Include a returned IP address or a complete address or alias line, not just `has` or `address`. The quest checks your reported answer, not captured DNS output. If DNS returns an error rather than an answer, ask for help; do not invent a record.

## Related Reading

- [S6 self-study](../sessions/S06/self-study.md)
- [host](../commands/host.md)
- [DNS](../concepts/dns.md)
- [network diagnostics](../concepts/network-diagnostics.md)
