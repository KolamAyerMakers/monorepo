# Publish troubleshooting notes

Quest: publish-http-troubleshooting

## Mission

Create `~/src/pages/troubleshooting.md` with notes on 200, 404, and 502.

## Commands You Will Use

- `micro`
- `build-website`

## Steps

1. Create `~/src/pages/troubleshooting.md`.
2. Add notes for HTTP 200, 404, and 502.
3. Run `build-website`.
4. Ask the guide to check the source file.

## Hints

1. 200 means success.
2. 404 means missing resource.
3. 502 usually means a bad gateway or backend problem.

## If Check Fails

Make sure the troubleshooting page mentions 200, 404, and 502.

## Related Reading

- [build-website](../commands/build-website.md)
- [status codes](../concepts/status-codes.md)
- [reverse proxy](../concepts/reverse-proxy.md)
- [multi-page sites](../concepts/multi-page-sites.md)
