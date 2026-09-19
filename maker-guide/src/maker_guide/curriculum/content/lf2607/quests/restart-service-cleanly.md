# Restart service cleanly

Quest: restart-service-cleanly

## Mission

Restart your own `site.service` deliberately and verify its actual local response, not just the command's exit status. Normal page edits need a build and reload, not a server restart.

## Commands You Will Use

- `systemctl --user`
- `curl`
- `journalctl --user`

## Steps

Use your classroom SSH account and the existing unit from [Enable your site service](enable-site-service.md). Confirm `$USER` is your classroom login and agree to the brief interruption before restarting your own service. Do not start a competing manual server.

If you changed the unit, first inspect it with `systemctl --user cat site.service` and run `systemctl --user daemon-reload`. Its Caddy file-server configuration should keep `WorkingDirectory=%h`, the all-interface listener on the assigned port, explicit `--root %h/public_html`, and `--access-log`. Use systemd, not `caddy stop` or `caddy reload`, which might target shared Caddy. Then:

```bash
systemctl --user restart site.service
systemctl --user status site.service --no-pager
PORT="$((10000 + $(id -u)))"
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
journalctl --user -u site.service --no-pager -n 50
```

Read the real HTTP status and recognizable page content, then match the request to the journal. Reload your [service homepage](https://your-handle.lf2607.kolamayermakers.org/) in your laptop browser, replacing `your-handle`. A local response does not prove the public route works.

If you use recorded progress, ask the guide to check your command history. A recorded restart and curl command do not independently prove recovery.

## Hints

1. Restart first, verify second.
2. Use the local port for a direct check.
3. Do not trust a restart without a request afterward.

## If Check Fails

For missing command evidence, run the restart and curl request above. For an actual failure, read the journal and repair the cause before retrying. Reload after unit edits; use `systemctl --user reset-failed site.service` only after repair if a start limit blocks recovery. Never kill an unknown listener, change the assigned port, or alter shared routing to hide the error. Bring local and public observations to staff if needed.

## Related Reading

- [systemctl](../commands/systemctl.md)
- [curl](../commands/curl.md)
- [systemd user services](../concepts/systemd-user-services.md)
- [manual web service](../concepts/manual-web-service.md)
