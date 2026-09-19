# S8 Self-Study: Keep Your Server Running

Session: S8

Date: 2026-09-26

## Study Path

Restart the S7 manual backend, stop it deliberately, and give the same job to a systemd user service. Preserve the unit when you create it, watch real requests, diagnose and repair one reversible failure, then test what happens after all logins close.

Allow 25 minutes for manual restart and handover, 45 for the unit and source preservation, 25 for requests and logs, a 10-minute break, 35 for repair, and 40 for logout and handoff. Two SSH connections are enough. Tmux and shell functions are optional, not prerequisites.

## Before You Begin

Use your own classroom account, existing source in `~/src`, and published site in `~/public_html`. Confirm `whoami` agrees with `$USER`. Keep the static homepage and existing report available; do not replace the project or rewrite an existing checker.

Before class, the instructor must confirm the public route, installed `/usr/bin/caddy`, user manager, and `Linger` for each account. The instructor also needs to establish a logout observation interval longer than the configured logout delay. If lingering is disabled, the instructor must arrange a policy decision or explicitly treat the exercise as observing shutdown, not promise that enabling a unit guarantees uptime. Learners do not run `sudo`, install packages, enable lingering, change shared routing, or bypass TLS verification.

Use the [S7 self-study route](../S07/self-study.md) if the backend and its two routes are unfamiliar. A working service hostname means a peer can actually load the page, not merely that a process exists.

## 1. Restart The Manual Server

Open two SSH connections from your laptop using your username:

```bash
ssh username@lf2607.kolamayermakers.org
```

If you already have a running user unit, inspect `systemctl --user status site.service --no-pager` and agree to the short outage before stopping it with `systemctl --user stop site.service`. Do not stop unknown processes or start a competing listener.

In the first SSH shell:

```bash
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
```

The course formula is `10000 + uid`; if the result exceeds `65535`, stop and ask the instructor. Never choose a replacement port. Otherwise start the backend:

```bash
caddy file-server --listen ":$PORT" --root "$HOME/public_html" --access-log
```

In the second SSH shell:

```bash
PORT="$((10000 + $(id -u)))"
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
```

Reload your [service homepage](https://your-handle.lf2607.kolamayermakers.org/) in the laptop browser, replacing `your-handle`. Watch the request in the first terminal. The foreground process occupies that shell and has no reliable service supervision across disconnects or reboots.

Now press `Ctrl-C` in the server terminal. This is the handover: **stop the manual server before systemd takes the same port**. Detaching from an optional tmux session does not stop it. `file-server` disables its admin API, avoiding an admin-port conflict with shared Caddy. Never use `caddy stop` or `caddy reload`: they can target shared Caddy's admin endpoint, not personal Caddy. Once supervised, control your process with `systemctl --user` only.

## 2. Create The User Unit

In an SSH shell:

```bash
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
/usr/bin/caddy version
mkdir -p ~/.config/systemd/user
ls -la ~/.config/systemd/user
```

If Caddy is unavailable at this path, ask the instructor. If `site.service` already exists, inspect its contents and any overrides before editing:

```bash
systemctl --user cat site.service
micro ~/.config/systemd/user/site.service
```

Exit without changing it until you understand the existing content and agree to the changes. If there are custom drop-ins or a different application, ask the instructor to adapt the exercise rather than replacing it with this template. Preserve an existing unit in a new private backup directory:

```bash
UNIT_BACKUP="$(mktemp -d "$HOME/site-unit-original.XXXXXX")"
cp ~/.config/systemd/user/site.service "$UNIT_BACKUP/site.service"
printf '%s\n' "$UNIT_BACKUP/site.service"
```

Continue only if the copy succeeded. Record the path outside the public pages. Unique directories avoid overwriting earlier backups. For a new unit, no previous file needs copying.

Open the unit:

```bash
micro ~/.config/systemd/user/site.service
```

For a new course unit, enter the following complete content. **Replace `12345` with the numeric port you printed**, not the name `PORT` or an arithmetic expression. For an existing course unit, make only the agreed changes and preserve unrelated settings.

```ini
[Unit]
Description=Personal website service

[Service]
WorkingDirectory=%h
ExecStart=/usr/bin/caddy file-server --listen :12345 --root %h/public_html --access-log
Restart=on-failure

[Install]
WantedBy=default.target
```

Save with `Ctrl-S`, then exit with `Ctrl-Q`.

- `%h` is systemd's home-directory specifier. `WorkingDirectory=%h` is stable even when the publisher replaces the entire `public_html` directory.
- `--root %h/public_html` explicitly selects the current published tree on new requests. A server relying on its working directory can stay attached to the old directory after publishing. Do not use `WorkingDirectory=%h/public_html` as a substitute for the explicit root.
- `--listen :12345` listens on all interfaces; the classroom firewall blocks new direct external connections to that port. Replace `12345` with your assigned number. Shared Caddy handles public HTTPS and forwards HTTP to `127.0.0.1` at that port. Personal Caddy needs no `--domain`. Same software, two separate processes; no Caddyfile or JSON configuration is needed.
- The pages are still public through shared Caddy. `--root` is not a sandbox: symlinks can lead outside it. Keep private files and symlinks to them out of the published tree. Without `--browse`, a directory without an index has no automatic listing.
- `--access-log` enables structured request logs, which systemd captures in the journal along with process messages.
- `ExecStart` does not run through Bash. Systemd does not evaluate `$(id -u)` or `$((...))`; use the literal numeric port.
- `Restart=on-failure` retries a process failure, not an intentional stop. It is not a guarantee that bad configuration will eventually work.
- `WantedBy=default.target` lets enablement attach the unit to your user manager's normal startup target. Enablement and lingering are separate.

## 3. Start And Request The Service

Confirm the manual server is stopped, then:

```bash
systemctl --user daemon-reload
systemctl --user enable --now site.service
systemctl --user status site.service --no-pager
```

`daemon-reload` rereads unit files but does not restart an existing process. `enable --now` arranges startup with your user manager and starts the unit now. If it was already running when you edited its unit, also run `systemctl --user restart site.service` to use the new definition. Keep `--user`: this unit belongs to your account, not root.

Read `Active:`. An `inactive` or `failed` result is a problem to diagnose, not a reason to report a running service. Status can exit nonzero for those states. If startup fails, read the journal and use the troubleshooting table below before proceeding.

```bash
PORT="$((10000 + $(id -u)))"
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
curl -I --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
```

Read the actual status and local body. Curl can exit successfully after an HTTP error. Local access tests personal Caddy; public-hostname curl from the classroom machine also uses shared Caddy but may use local hostname mappings. Shared Caddy is a server to curl and a client to personal Caddy. Open the service homepage in your laptop browser and invite a peer to confirm outside access and recognizable content.

## 4. Preserve The Working Unit

Save a source copy now, not at the end of S9. Put it outside `pages` so the unit does not become a public page:

```bash
mkdir -p ~/src/services
ls -la ~/src/services
```

If `~/src/services/site.service` already exists, read it before replacing anything. Only with your consent to update that copy:

```bash
cp -i ~/.config/systemd/user/site.service ~/src/services/site.service
git -C ~/src status
git -C ~/src diff -- services/site.service
git -C ~/src diff --cached
```

Use the existing `~/src` repository; if absent, follow [S7 source preservation](../S07/self-study.md#6-preserve-source-now). Read new file content in the editor too, since unstaged diff omits untracked files. If unrelated changes are already staged, preserve them and ask before continuing. Otherwise:

```bash
git -C ~/src add -- services/site.service
git -C ~/src diff --cached
```

Only if the entire staged diff contains the intended working unit and no credentials:

```bash
git -C ~/src commit -m "Keep my website user service"
git -C ~/src status
```

The source copy is not the installed unit. Editing it alone does not change the service. Document the installed path `~/.config/systemd/user/site.service` in your setup notes. Do not stage private backup directories, generated output, or unrelated work. No push is required.

## 5. Follow Real Requests

In one SSH shell:

```bash
journalctl --user -u site.service -f
```

In the other:

```bash
curl -i --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
curl -i --max-time 10 "https://$USER.lf2607.kolamayermakers.org/missing-s8-page.html"
```

Ask a peer to visit the service homepage and an agreed nonexistent path from their browser too. Match structured access-log fields `request.method`, `request.uri`, `status`, and the timestamp or time (`ts` in JSON) to these visits. JSON in the journal can look different from the foreground terminal; do not expect an identical line format. A missing path should produce `404`, not a failed unit. The logged client may be `127.0.0.1` because shared Caddy is personal Caddy's direct client; it is not proof of a visitor's identity. Browser caches and extra requests can make the sequence less tidy than one click per line.

Press `Ctrl-C` in the follower shell, then read the retained lines:

```bash
journalctl --user -u site.service --no-pager -n 20
```

Only the follower stopped. Reload the service homepage to confirm personal Caddy still serves it. Do not publish raw logs containing private request data; summarize relevant paths and errors.

## 6. Publish Without A Service Restart

Open `~/src/pages/setup.md` in Micro. If absent, create it with a `# My Setup` heading; S7 did not require this page. Otherwise preserve existing notes. Add the unit path, the assigned numeric port, and these distinctions in your own words:

```markdown
## Keeping My Server Running

My installed unit is ~/.config/systemd/user/site.service.
My source copy is services/site.service in my source repository.
I use systemctl --user start site.service and systemctl --user stop site.service
to control the service. Its journal is available with journalctl --user -u site.service.
I never use caddy stop or caddy reload; they can target shared Caddy.

After changing the installed unit, I run daemon-reload and restart the service.
After changing page source, I run build-website and reload the browser instead.
The unit keeps WorkingDirectory=%h and serves --root %h/public_html.
```

Add the homepage's `[My setup](setup.html)` link and setup's `[Home](index.html)` link if missing, without duplicating existing links. Save, then:

```bash
build-website
```

After a successful build, browse `setup.html` through the static and service routes and ask a peer to find your new explanation. **Do not restart the service.** This demonstrates that the unit continues serving the newly replaced publication directory. Use a fresh browser reload if needed; repair build failures rather than relying on old output.

Review and commit only the intended page source changes using the S7 Git workflow. Operational notes are public: no credentials, private links, or private backup contents.

## 7. Break And Read The Error

Take a break first. This is a brief, agreed interruption to **your own working course unit only**. If you do not consent to an outage, observe a consenting peer or the instructor's demonstration instead. Do not break another learner's service. If your unit has custom content or drop-ins, ask the instructor to choose a safe equivalent rather than overwriting it.

Confirm the service and public page work. In one SSH shell, inspect the effective unit and create a unique backup:

```bash
systemctl --user cat site.service
BACKUP="$(mktemp -d "$HOME/site-service-backup.XXXXXX")"
cp ~/.config/systemd/user/site.service "$BACKUP/site.service"
printf '%s\n' "$BACKUP/site.service"
```

Continue only after the copy succeeds. Record that exact path in private notes, and keep this shell open so `BACKUP` remains set. Previous backups are untouched. Stop the unit, then open it:

```bash
systemctl --user stop site.service
micro ~/.config/systemd/user/site.service
```

Change **only** `/usr/bin/caddy` in `ExecStart` to `/no/such/caddy`. This deliberate nonexistent executable does not change the port, published files, or other settings. Save, then:

```bash
systemctl --user daemon-reload
systemctl --user restart site.service
systemctl --user status site.service --no-pager
journalctl --user -u site.service --since "5 minutes ago" --no-pager
systemctl --user stop site.service
```

The restart or status command may fail; continue to read the journal. Expect an executable failure, often `203/EXEC` with a missing-file message. Automatic retries may also reach a start limit. Read the specific recent message you actually got, then stop the unit to end retries. Explain how the changed path caused the observed error before repairing. Do not leave the failed unit for later.

## 8. Restore And Recover

In the same SSH shell, inspect exactly what changed:

```bash
diff -u "$BACKUP/site.service" ~/.config/systemd/user/site.service
```

Differences are expected; `diff` exits `1` when files differ. If there are changes beyond your deliberate typo, preserve those edits and ask before restoring the whole file. If the only change is the agreed break, restore the saved working content:

```bash
cp -i "$BACKUP/site.service" ~/.config/systemd/user/site.service
```

At the prompt, consent to replacing your broken unit with that verified backup. If the shell was lost, recover the exact recorded backup path first; do not guess which backup is newest or overwrite a unit with an unrelated copy.

```bash
systemctl --user daemon-reload
systemctl --user reset-failed site.service
systemctl --user restart site.service
systemctl --user status site.service --no-pager
PORT="$((10000 + $(id -u)))"
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
curl -I --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
curl -I --max-time 10 "https://lf2607.kolamayermakers.org/~$USER/"
```

`reset-failed` clears failure state and the start-rate counter from the deliberate break. It does not fix a bad unit; restore first. Rereading the definition alone does not start personal Caddy, so restart and verify real responses. Reload both public homepages in your laptop browser and invite a peer. Recovery means the page is back, not merely that a command returned.

Keep the private backup until you are satisfied with recovery. Do not copy the broken version into source control. Record the observed error, cause, repair, and result in `setup.md` without dumping private logs.

## 9. Test Logout Survival

The instructor handles questions about lingering and logout policy. Before logging out:

```bash
loginctl show-user "$USER" -p Linger
systemctl --user show site.service -p MainPID -p ExecMainStartTimestamp
```

`Linger=yes` allows the user manager to run without a login. `Linger=no` means it may stop after the last logout. Enabling `site.service` does not enable lingering and cannot promise logout survival. If lingering is off or the instructor has not confirmed the observation interval, ask the instructor; do not run `loginctl enable-linger` or use `sudo` yourself.

Record `MainPID` and `ExecMainStartTimestamp` in notes available on your laptop. Agree with the instructor how long to stay logged out so the observation exceeds the configured user-manager logout delay. Then:

1. Close **all** SSH connections, browser terminals, remote editor connections, and other logins for your account. A second open login invalidates the experiment.
2. If you used optional tmux, end your own shells rather than merely detaching. Do not end anyone else's sessions. Ask the instructor to confirm no account login remains if uncertain.
3. In the last SSH shell, outside tmux, run `exit`.
4. Stay logged out for the agreed interval. Reload the service homepage freshly in the laptop browser and ask a peer to request it too. Avoid cached content; do not reconnect before this observation.
5. Reconnect and compare the process identity and start time:

```bash
ssh username@lf2607.kolamayermakers.org
systemctl --user status site.service --no-pager
systemctl --user show site.service -p MainPID -p ExecMainStartTimestamp
```

An enabled unit can start again on login. `active` after reconnecting alone does not prove it survived logout. Changed process identity or start time indicates a restart; use the journal to investigate rather than guessing. Outside responses while logged out plus unchanged identity support uninterrupted operation during that observed interval, not a promise of indefinite uptime or a reboot test.

If it stopped, record that honestly, ask the instructor about lingering or policy, and restore your own service with `systemctl --user start site.service` if needed. Confirm page access before leaving.

## Troubleshooting

| Observation | Next action |
| --- | --- |
| Unit not found | Check `~/.config/systemd/user/site.service`, then run `daemon-reload`. |
| `203/EXEC` or failed at step EXEC | Inspect the executable path and recent journal. Restore `/usr/bin/caddy` if that was the agreed typo. |
| Failed at step CHDIR | The configured working directory is missing or inaccessible. Use `WorkingDirectory=%h`; ask the instructor about home access rather than broadening permissions. |
| `address already in use` | Stop your manual server with `Ctrl-C` in its terminal. Do not pick another port or kill another learner's process. |
| Start request repeated too quickly | Fix the cause, then `reset-failed` and restart. |
| Active but HTTP `404` | Inspect the explicit publication path and source, including the homepage index; build and reload. Do not add `--browse` to hide a missing index. Active is not proof of correct content. |
| Old content after publishing | Confirm stable `WorkingDirectory=%h` and explicit `--root %h/public_html`, successful build, and fresh browser reload. Correcting a unit needs reload and restart; normal content changes do not. |
| Local page works, public service is `502` | Compare the numeric port with the course formula, then bring the results to the instructor for proxy diagnosis. |
| DNS or TLS error | This is not HTTP `502`. Bring the exact error and local result to the instructor; do not change shared routing or bypass certificates. |
| Service stops after logout | Confirm all logins closed, observation timing, lingering, and journal with the instructor. Enablement alone is not enough. |

## Peer Handoff And Notes

Update `setup.md` with the service lifecycle, real request observations, diagnosis and recovery, logout result, and one useful peer comment. Ask before naming the peer publicly. Build and browse the notes without restarting, then commit only the intended source changes after reviewing the complete staged diff. Preserve unrelated staged work and never commit credentials.

Success means your peer can load the supervised site, you can match a request to the journal, recover your own broken unit, and explain what the logout experiment actually established. Keep the working source copy of the unit synchronized if you made a lasting repair, using the earlier consent and review steps. No helper dispatcher or tmux lifecycle is required.

## Optional Practice

- [Watch service logs](../../quests/watch-service-logs.md) for another visitor/request experiment.
- [Document your service port](../../quests/document-service-port.md) to improve the existing operational notes.
- [Write site helper functions](../../quests/write-site-helper-functions.md) only if a repeated command merits a name. No service depends on this extension.
- [Tmux command reference](../../commands/tmux.md) if you want a detachable terminal. Tmux does not replace service supervision or establish logout survival.
- [Systemd service documentation](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html) and [journalctl documentation](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html) for the underlying tools.

## Next Session

S9: **2026-10-10**, Automate It. Hand It Over. Bring your working service, source history, operational notes, and any unresolved routing or logout issue.
