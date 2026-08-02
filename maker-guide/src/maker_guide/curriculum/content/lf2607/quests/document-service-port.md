# Document your service port

Quest: document-service-port

## Mission

Create `~/src/pages/service.md` explaining how your user port is computed.

## Commands You Will Use

- `id -u`
- `micro`
- `build-website`

## Steps

1. Run `id -u`.
2. Create `~/src/pages/service.md`.
3. Explain the port rule for your account.
4. Run `build-website`.

## Hints

1. Your port is based on your numeric user id.
2. Mention either `10000 + uid` or the word port.
3. Save source before rebuilding.

## If Check Fails

Update `~/src/pages/service.md` so it explains the user port rule.

## Related Reading

- [id -u](../commands/id-u.md)
- [build-website](../commands/build-website.md)
- [manual web service](../concepts/manual-web-service.md)
- [platform reference](../guides/platform-reference.md)
