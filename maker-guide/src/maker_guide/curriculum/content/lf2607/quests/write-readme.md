# Write your README

Quest: write-readme

## Mission

Write an operations README that a peer can use to understand, refresh, inspect, and recover your existing site. Test the instructions together, repair ambiguities, then preserve the README with the source handoff.

## Write For The Next Operator

Open `micro ~/src/README.md`, keeping useful existing content. Save with `Ctrl-S` and quit with `Ctrl-Q`. Include:

- The site's purpose, its static and service public links, and the report page. Use actual usernames in Markdown links; `$USER` does not expand in prose or a browser address bar.
- Source in `~/src`, generated output in `~/public_html`, two working scripts in `~/scripts`, and three active units in `~/.config/systemd/user`. Include the [handoff path table](prepare-source-handoff.md#copy-working-files).
- Required tools and project dependencies, including Caddy at `/usr/bin/caddy` and Node/npm (the build unit uses `/usr/local/bin/npm`), the classroom numeric port formula `10000 + uid`, and hostnames/executable paths to adapt on another machine. Install locked project dependencies with `npm ci` during restoration.
- The refresh/build chain: `systemctl --user start site-build.service` runs `maker-report.sh "System Report"` before npm. The report collects facts; the builder alone does not. A failed report must stop the build and preserve the last valid result.
- Timer control, logs, and how to pause automation and wait for a running build before editing source, building manually, or committing. Include `systemctl --user stop site-build.timer` and the hourly restart procedure.
- Runnable web-service start/stop/status/log commands, local and public request commands, and what failure looks like. Include `bash ~/scripts/site-check.sh "" maker-report.html` for the static homepage and report, not as proof of the service route.
- [Restoration from source](prepare-source-handoff.md#restore-from-source), including copying scripts and units back, the numeric assigned port, all-interface listener, `WorkingDirectory=%h`, `--root %h/public_html`, and `--access-log`. Explain that the classroom firewall blocks new direct external connections to the backend port, while shared Caddy forwards public HTTPS requests over loopback HTTP. No Caddy configuration file is needed; `file-server` disables the admin API. Use `systemctl --user`, never `caddy stop` or `caddy reload`, which might target shared Caddy. Reload unit changes and restart a running web service to apply them.
- One real failure: symptom, evidence, cause, repair, and the response or content that confirmed recovery.

Use [S9 self-study](../sessions/S09/self-study.md) for runnable automation instructions. Explain commands in your own project's README rather than leaving only vague words such as "build" or "fix".

## Peer Operation Test

The peer reads and directs from the README. The owner reviews and types every command in their own account. No passwords, keys, or tokens change hands; do not operate in the peer's login.

1. Ask the peer to find the public site, source repository, and working script/unit paths using only the README.
2. Follow the documented pause-and-wait procedure, refresh/build once through `site-build.service`, and inspect actual logs and changed report facts.
3. Agree to a brief outage of the owner's personal web service. Do not delete pages, break the report generator, or alter shared routing.
4. Stop and recover that service using the README. Compare the local request before and after recovery, then check the public service route and laptop browser.
5. Note one missing or ambiguous instruction, amend the README, and repeat that part without spoken hints. Swap roles.

If you need fallback commands for the agreed stop/recovery, run these in the owner's classroom account, one step at a time:

```bash
service_port="$((10000 + $(id -u)))"
systemctl --user stop site.service
curl --max-time 10 -fsS "http://127.0.0.1:$service_port/"
systemctl --user start site.service
systemctl --user status site.service --no-pager
journalctl --user -u site.service --no-pager -n 20
curl --max-time 10 -fsS "http://127.0.0.1:$service_port/"
curl --max-time 10 -fsS "https://$USER.lf2607.kolamayermakers.org/"
```

The first curl is expected to fail because you intentionally stopped the listener. If it succeeds, inspect what is serving that port rather than claiming the stop worked. After restart, requests must return the intended page; status alone is not recovery evidence. If recovery fails, inspect the unit and journal with staff and restore service before leaving. Do not kill unknown processes or pick another learner's port.

Restart the hourly build timer when operation testing is finished, or leave it paused only while you immediately complete the source handoff. Record the interruption, recovery evidence, and wording fixed, without secrets.

## Preserve The Result

Follow [Prepare a source handoff](prepare-source-handoff.md#inspect-commit-push): pause and wait, inspect all intended files, stage explicit paths, commit, push, and verify the README and working-file copies in Forgejo. A readable local README alone is not a recoverable off-machine handoff.

## Related Reading

- [README writing](../concepts/readme-writing.md)
- [Forgejo publishing](../concepts/forgejo-publishing.md)
