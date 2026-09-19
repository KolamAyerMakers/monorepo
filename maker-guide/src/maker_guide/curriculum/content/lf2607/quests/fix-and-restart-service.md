# Fix And Restart Service

Quest: fix-and-restart-service

## Mission

Recover your own backend from an observed failure and confirm that a peer can load the page again. Do not break a healthy service merely to have something to repair; use the [consensual break lab](break-and-read-error.md) only if you want that practice.

## Diagnose Before Editing

```bash
systemctl --user status site.service --no-pager
journalctl --user -u site.service --since "10 minutes ago" --no-pager
systemctl --user cat site.service
```

Read actual state and errors. Use the smallest repair that explains them:

| Observation | Repair direction |
| --- | --- |
| Failed at step EXEC | Restore the intended executable path; the course uses `/usr/bin/caddy`. |
| Failed at step CHDIR | Inspect home access and the stable `WorkingDirectory=%h`; do not broaden permissions or remove safety settings. |
| `Address already in use` | Stop your own manual server in its terminal. Do not kill another learner's process or choose another port. |
| Active with HTTP `404` | Repair the requested path or build the source; a missing index returns `404` with browsing disabled. A service restart is not a content repair. |
| Local page works but public route fails | Compare the assigned port and ask staff about routing; do not change shared DNS, shared Caddy, or TLS verification. |

Before editing an existing unit, agree to the interruption and preserve its current content in a unique private backup as in the [unit preservation steps](../sessions/S08/self-study.md#2-create-the-user-unit). If recovering from the deliberate break, compare the known working backup first and consent to restoring it; preserve unrelated changes and existing backups. Do not replace a customized unit wholesale with a template.

The course contract keeps `WorkingDirectory=%h` and `ExecStart=/usr/bin/caddy file-server --listen :12345 --root %h/public_html --access-log`, replacing `12345` with your literal result of `10000 + uid`. The publisher replaces `public_html`, so cwd-only serving is not sufficient. No configuration file or `sudo` is needed. Use `systemctl --user`, not `caddy stop` or `caddy reload`: those commands might target shared Caddy.

## Apply The Repair

After repairing the installed unit:

```bash
systemctl --user daemon-reload
systemctl --user reset-failed site.service
systemctl --user restart site.service
systemctl --user status site.service --no-pager
```

`daemon-reload` rereads the definition; `restart` applies it to a new process. `reset-failed` clears failure and start-limit state if retries exhausted the allowance. It does not fix the cause.

If you only changed page source, run `build-website` and reload the browser instead. **Do not restart for ordinary served-content changes.**

## Confirm Recovery

```bash
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
```

If this exceeds `65535`, ask staff rather than picking another port. Otherwise:

```bash
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
curl -I --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
curl -I --max-time 10 "https://lf2607.kolamayermakers.org/~$USER/"
```

Read actual statuses and content. Open your [service homepage](https://your-handle.lf2607.kolamayermakers.org/) and [static homepage](https://lf2607.kolamayermakers.org/~your-handle/) in the laptop browser, replacing `your-handle`, and invite a peer. A successful restart command alone is not recovery. If it still fails, read the new journal entries rather than repeating restarts blindly.

## Preserve The Result

Add the cause, repair, and outcome to existing `setup.md`. Build and browse the notes without restarting. If the installed unit changed permanently, update its source copy using the [reviewed preservation workflow](../sessions/S08/self-study.md#4-preserve-the-working-unit). Commit only intended source files, preserving unrelated staged work; no credentials, broken units, or private backups. Ask before naming a peer publicly.

## Related Reading

- [Enable site.service](enable-site-service.md)
- [Watch service logs](watch-service-logs.md)
- [Systemd user services](../concepts/systemd-user-services.md)
