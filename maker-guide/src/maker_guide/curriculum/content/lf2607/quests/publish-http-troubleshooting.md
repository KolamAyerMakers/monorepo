# Publish Troubleshooting Notes

Quest: publish-http-troubleshooting

## Mission

Turn your real server observations into a short operational reference in `setup.md`. This is optional publishing reinforcement. If `~/src/pages/setup.md` is absent, follow [Create a setup page](create-setup-page.md) first, creating source before building. Preserve existing files and links. A separate troubleshooting page is optional; do not duplicate a working explanation just to create another file.

## Write What Helped

```bash
micro ~/src/pages/setup.md
```

Preserve existing notes. Add a heading such as `## HTTP Troubleshooting` and use the following table as a starting point. Replace general descriptions with the paths, causes, and recovery you actually observed; mark anything not yet observed rather than inventing it.

| Symptom | Meaning | Useful next action |
| --- | --- | --- |
| HTTP `200` | Request succeeded, but it may still be the wrong content | Confirm the recognizable page and recent source change |
| HTTP `404` | Server answered but the path or directory index was absent | Check the path and source, build, then reload; do not enable browsing to hide missing output |
| Local connection refused | No listener accepted the connection; no HTTP response | Check your backend process and assigned port |
| Public service HTTP `502` | Proxy could not get a usable backend response | Compare local access with backend state and numeric port |
| DNS or TLS error | Failure before an HTTP response | Bring the actual error and local result to staff |
| Old content after editing | Save, build, or browser freshness may be missing | Resolve the build and reload freshly; do not restart routinely |

Explain why shared Caddy's static route can stay available while the service route to personal Caddy is broken: two processes, with public HTTPS at the shared proxy and plain HTTP at your backend. Include one specific incident and its successful recovery, not just status definitions. If using systemd, note that the unit keeps `WorkingDirectory=%h` and explicit `--root %h/public_html` because the publisher replaces the directory. Record how `--access-log` fields such as `request.uri`, `request.method`, `status`, and time helped locate the request.

Do not publish passwords, tokens, private keys, private setup links, or raw logs containing private request data. Do not recommend `sudo`, shared routing changes, serving a broader directory, or bypassing certificate verification.

## Publish And Let A Peer Use It

Keep the homepage's `[My setup](setup.html)` link and setup's `[Home](index.html)` link. If you already have `troubleshooting.md`, preserve it and link it from setup instead of maintaining contradictory copies.

```bash
build-website
```

After success, follow the links from your laptop browser. When the backend is running, confirm the notes through both static and service routes without restarting it. Ask a peer to use the page to choose a next action for one real symptom. Revise any confusing advice and record useful peer feedback, naming them only with consent.

Use the [source preservation workflow](../sessions/S07/self-study.md#6-preserve-source-now) to review and commit only the intended page changes now. If you maintained a separate page, stage that explicit path as well. Preserve unrelated staged work; do not commit generated output or credentials.

Success means someone can use your notes to locate a failure and recover safely, not merely find the numbers `200`, `404`, and `502` in a file.

## Related Reading

- [Explain a 502](explain-502.md)
- [Fix and restart service](fix-and-restart-service.md)
- [HTTP status codes](../concepts/http-status-codes.md)
- [Multi-page sites](../concepts/multi-page-sites.md)
