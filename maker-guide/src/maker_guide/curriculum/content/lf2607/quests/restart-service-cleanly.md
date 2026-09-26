# Restart service cleanly

Quest: restart-service-cleanly

## Mission

Restart your own `site.service` deliberately and verify its actual local response, not just the command's exit status. Normal page edits need a build and reload, not a server restart.

## Commands You Will Use

- `systemctl --user`
- `curl`
- `journalctl --user`

## Steps

Use your classroom SSH account and the existing unit from [Enable your site service](enable-site-service.md). Restarting briefly stops your server; it does not affect anyone else's service. Do not start a competing manual server.

If you changed the unit, first [verify and reload it](../sessions/S08/self-study.md#8-restore-and-recover). Use `systemctl --user`, not `caddy stop` or `caddy reload`, which might target shared Caddy. Then:

```bash
systemctl --user restart site.service
systemctl --user status site.service
curl -i "http://127.0.0.1:$((10000 + $(id -u)))/"
journalctl --user -u site.service --since "5 minutes ago"
```

Press `q` to leave each paged view. Read the HTTP status and page content, then match the request to the journal. Reload your [service homepage](https://your-handle.lf2607.kolamayermakers.org/) in your laptop browser, replacing `your-handle`. A local response does not prove the public route works.

If you use recorded progress, ask the guide to check your command history. A recorded restart and curl command do not independently prove recovery.

## If Check Fails

For missing command evidence, run the restart and curl request above. For an actual failure, read the journal and repair the cause before retrying. Reload after unit edits; use `systemctl --user reset-failed site.service` only after repair if a start limit blocks recovery. Never kill an unknown listener, change the assigned port, or alter shared routing to hide the error. Bring local and public observations to staff if needed.

## Related Reading

- [systemctl](../commands/systemctl.md)
- [curl](../commands/curl.md)
- [systemd user services](../concepts/systemd-user-services.md)
- [manual web service](../concepts/manual-web-service.md)
