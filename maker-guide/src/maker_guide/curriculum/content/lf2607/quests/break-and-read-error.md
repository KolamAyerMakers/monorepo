# Break And Read The Error

Quest: break-and-read-error

## Mission

Make one reversible change to your own working course unit, diagnose the actual error, then restore page access before finishing.

## Agree And Preserve

Agree to the brief outage first. If you do not consent, observe a consenting peer or staff demonstration instead. Never break another learner's service. Confirm your own local and public page work before starting, and inspect the effective unit:

```bash
systemctl --user cat site.service
```

If there are custom settings or a different application, ask staff to adapt the exercise; do not overwrite them with a template. In one SSH shell, create a unique private backup:

```bash
BACKUP="$(mktemp -d "$HOME/site-service-backup.XXXXXX")"
cp ~/.config/systemd/user/site.service "$BACKUP/site.service"
printf '%s\n' "$BACKUP/site.service"
```

Continue only if the copy succeeds. Record the exact path in private notes, and keep this shell open through recovery so `BACKUP` remains set. Existing backups stay untouched.

## Change One Path

```bash
systemctl --user stop site.service
micro ~/.config/systemd/user/site.service
```

Change only `/usr/bin/caddy` in `ExecStart` to `/no/such/caddy`. Preserve the numeric port, `WorkingDirectory=%h`, all-interface listener, explicit `--root %h/public_html`, `--access-log`, and all other content. Save, then:

```bash
systemctl --user daemon-reload
systemctl --user restart site.service
systemctl --user status site.service --no-pager
journalctl --user -u site.service --since "5 minutes ago" --no-pager
systemctl --user stop site.service
```

Restart or status may fail; continue to read the journal. Expect an executable failure, often `203/EXEC` and a missing-file message. Retries may also hit a start limit. Read the actual recent error, not a memorized answer. The final stop ends retries.

Explain to a peer how the changed executable path led to that message. Do not change ports, permissions, shared routing, or published files to make the error disappear. No `sudo` or process-wide kill commands.

## Restore Before Finishing

Inspect the difference:

```bash
diff -u "$BACKUP/site.service" ~/.config/systemd/user/site.service
```

Differences are expected. If there are edits beyond your typo, preserve them and ask before replacing the file. Otherwise, consent to restoring your saved working unit at the copy prompt:

```bash
cp -i "$BACKUP/site.service" ~/.config/systemd/user/site.service
systemctl --user daemon-reload
systemctl --user reset-failed site.service
systemctl --user restart site.service
systemctl --user status site.service --no-pager
PORT="$((10000 + $(id -u)))"
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
curl -I --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
```

Use the already-verified course port; if it exceeds `65535`, ask staff rather than choosing another. If this shell was lost, recover the exact backup path you recorded before copying anything. `reset-failed` clears failure and retry-limit state; it does not repair the unit by itself.

Open your [service homepage](https://your-handle.lf2607.kolamayermakers.org/) and [static homepage](https://lf2607.kolamayermakers.org/~your-handle/) in the laptop browser, replacing `your-handle`. Invite a peer to confirm recovery. Do not leave a deliberate break behind; use [Fix and restart service](fix-and-restart-service.md) if it still fails.

## Keep The Diagnosis

Improve existing `setup.md` with the actual failure, cause, repair, and observed recovery. Build and [preserve only the intended source change](../sessions/S07/self-study.md#6-preserve-source-now). Keep the broken unit and private backups out of Git and public pages. No credentials or raw private logs; ask consent before naming a peer.

Success means you can connect the observed error to its cause and the page works again, not simply that an error appeared.

## Related Reading

- [S8 repair lab](../sessions/S08/self-study.md#7-break-and-read-the-error)
- [Journalctl](../commands/journalctl.md)
- [Systemctl](../commands/systemctl.md)
