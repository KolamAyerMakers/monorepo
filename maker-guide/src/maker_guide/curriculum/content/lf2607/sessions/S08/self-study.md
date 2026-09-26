# S8 Self-Study: Keep Your Server Running

Session: S8

Date: 2026-09-26

## Study Path

Give the S7 server's job to systemd: create its instructions, start it, and check your page. Test logout, follow requests, publish a change, then solve five service mysteries.

Use your classroom SSH account and existing site. Keep source in `~/src` and generated pages in `~/public_html`. Work only on your own service: no `sudo`, shared Caddy changes, or TLS bypasses.

## 1. Let systemd Run Your Server

The SSH server is already running before you connect. During startup, the **kernel**, Linux's core, starts **PID 1**. This process has the **init** role: bringing up the rest of the system.

On our machine, **systemd** fills that role. It starts and supervises **services**, programs managed independently of your terminal. Other init systems exist. Inspect process 1 from your SSH shell:

```bash
ps -p 1
```

The **system manager** handles machine-wide services such as SSH. A separate **user manager** handles your account's services. `systemctl --user` talks to that manager, without changing anyone else's services.

A **unit file** holds systemd's instructions. A service unit's filename ends in `.service`; ours is `site.service`.

If your manual Caddy is still running, stop it with `Ctrl-C` in its terminal before starting the service. Never use `caddy stop` or `caddy reload`: they can target shared Caddy.

## 2. Create The User Unit

User unit files live in `~/.config/systemd/user/`. Print your assigned port, then open the file:

```bash
echo "$((10000 + $(id -u)))"
mkdir -p ~/.config/systemd/user
micro ~/.config/systemd/user/site.service
```

If the port exceeds `65535`, ask the instructor rather than choosing another. If the file already exists, read it first and preserve unrelated settings; ask for help if it runs a different application.

`ExecStart` is the command; `%h` means your home directory. This is not Bash: replace `12345` with the printed number, not `$PORT` or a shell calculation.

```ini
[Unit]
Description=Personal website service

[Service]
WorkingDirectory=%h
ExecStart=/usr/bin/caddy file-server \
  --listen :12345 --root %h/public_html \
  --access-log
Restart=on-failure

[Install]
WantedBy=default.target
```

Save with `Ctrl-S`, then exit with `Ctrl-Q`. A trailing `\` continues the instruction onto the next line.

- `WorkingDirectory=%h` starts Caddy in your home. Keep the explicit `--root %h/public_html`: publishing replaces that directory, and Caddy must read the new files rather than stay in the old directory.
- `--access-log` records requests. Systemd collects these and Caddy's other messages in the journal.
- `Restart=on-failure` retries a failed process, not a deliberate stop.
- `WantedBy=default.target` lets `enable` add the service to your user manager's normal startup group. Writing this line does not start it.

Shared Caddy still handles public HTTPS and forwards to your port; personal Caddy serves HTTP. Do not add `--domain`. The published root is not a sandbox: keep private files and symlinks to them out of `public_html`.

## 3. Start And Request The Service

**systemd-analyze** checks the unit without starting it:

```bash
systemd-analyze --user verify ~/.config/systemd/user/site.service
```

Fix reported mistakes, including warnings, save, and check again. Verification can catch unknown settings and missing programs, but it does not check Caddy's arguments or your page.

`daemon-reload` reads the saved unit. `start` runs it now; `enable` arranges startup whenever your user manager starts. `status` shows its state:

```bash
systemctl --user daemon-reload
systemctl --user start site.service
systemctl --user enable site.service
systemctl --user status site.service
```

Look for `Active: active (running)`. Press `q` to leave the status view. If startup failed, use [Troubleshooting](#troubleshooting). If you edited an already-running unit, use `systemctl --user restart site.service` after `daemon-reload`; reloading alone does not change the running process.

Test your Caddy directly, then the public service route:

```bash
curl -i "http://127.0.0.1:$((10000 + $(id -u)))/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
```

Read the HTTP statuses and your page's HTML in the local response. An active process or HTTP `200` alone does not prove it is the right page. Open your [service homepage](https://your-handle.lf2607.kolamayermakers.org/) on your laptop, replacing `your-handle`.

Now [test logout survival](#9-test-logout-survival), as in the slides, then continue with [requests and logs](#5-follow-real-requests). Keep the working unit using the next section when you finish.

## 4. Preserve The Working Unit

Keep a copy outside `pages`, so it does not become a public page. Read any existing source copy before replacing it; preserve personal changes.

```bash
mkdir -p ~/src/services
cp -i ~/.config/systemd/user/site.service ~/src/services/site.service
```

`cp -i` asks before replacing a file. Review and commit the working copy with the [S7 source-preservation workflow](../S07/self-study.md#6-preserve-source-now); do not include unrelated work, generated output, credentials, or private logs.

The copy is not the installed unit. Editing `~/src/services/site.service` alone does not change the running service. Update the copy after any lasting repair.

## 5. Follow Real Requests

First try controlling your service. Run these one at a time and reload the service homepage after each:

```bash
systemctl --user stop site.service
systemctl --user start site.service
```

An intentional stop stays stopped, even with `Restart=on-failure`.

The **journal** stores messages from your service. **journalctl** reads it; `--since` selects how far back to look:

```bash
journalctl --user -u site.service --since "5 minutes ago"
```

Press `q` to leave. To watch new messages arrive, use `-f`:

```bash
journalctl --user -u site.service -f
```

Ask a peer to visit your service homepage, then `/missing.html` on the same site. Find each request's time (`ts` in JSON), `request.method`, `request.uri`, and `status`. A `404` for a missing page is a response from a running server, not a failed service. Shared Caddy may appear as the local client address; that does not identify the visitor.

Press `Ctrl-C` to stop following, then reload the homepage. Caddy should still respond: you stopped `journalctl`, not the service.

## 6. Publish Without A Service Restart

Caddy reads files from disk for each request. Edit an existing page under `~/src/pages`, save, then publish:

```bash
build-website
```

After a successful build, reload that page in your browser and find the change. No service restart is needed. Keep editing the source, not generated files in `public_html`.

## 7. Break And Read The Error

The guide has five mysteries, one at a time. It changes your service or published files, never your source in `~/src` or anyone else's site. Start from a working site and launch the current challenge in your classroom shell:

```bash
guide now
```

While a challenge is open, later `guide now` calls inspect it without breaking it again. Do not add another fault yourself.

Investigate before editing. `systemctl cat` shows the unit instructions; compare them with the state, recent journal, and local response:

```bash
systemctl --user cat site.service
systemctl --user status site.service
journalctl --user -u site.service --since "5 minutes ago"
systemd-analyze --user verify ~/.config/systemd/user/site.service
curl -i "http://127.0.0.1:$((10000 + $(id -u)))/"
```

Press `q` to leave each paged view. Did the process fail to start, did the connection fail, or did the server return an unexpected page? Read the first relevant error, not just a later retry-limit message.

Stuck? Run `guide` and ask a question. It reads fresh diagnostics and offers one hint at a time, not a full solution. No output pasting is needed.

## 8. Restore And Recover

Make the smallest repair that explains what you observed. For a unit problem, edit `~/.config/systemd/user/site.service`, preserving unrelated settings. Verify the saved file before applying it:

```bash
systemd-analyze --user verify ~/.config/systemd/user/site.service
```

Fix any reported mistakes first. `daemon-reload` rereads the unit; `restart` runs the corrected command:

```bash
systemctl --user daemon-reload
systemctl --user restart site.service
```

If the journal says retries reached the start limit, run `systemctl --user reset-failed site.service` before restarting. This clears the limit, not the cause. For a published-file problem, check the source and build output instead of repeatedly restarting Caddy.

Repeat the status and local page checks, then reload your service homepage in the browser. Recovery means your page is back, not just that a command succeeded.

Explain **what caused the failure and why your repair worked**:

```bash
guide answer 'Your cause and repair explanation'
```

One short sentence is enough; you can also answer in the interactive guide. Each challenge needs both a working local site and your explanation. There is no skip. After completion, run `guide now` for the next mystery.

Finish all five with your site working. [Preserve the working unit](#4-preserve-the-working-unit) and keep short notes on the causes and repairs, without credentials or private logs. Publishing notes is optional.

## 9. Test Logout Survival

Before leaving SSH, inspect the service:

```bash
systemctl --user status site.service
```

Keep `Main PID` and the date and time after `since` on the `Active:` line in notes on your laptop. Press `q` to return to the shell.

1. Close all your SSH connections.
2. Refresh your service homepage in your laptop browser **before reconnecting**. Does it still load?
3. Reconnect, run the same status command, and compare the PID and activation time.

Changed values mean Caddy restarted. A page that worked while you were away, with both values unchanged, is evidence it kept running during the test. `active` after reconnecting alone could hide a restart.

Submit what you observed and what it means with `guide answer 'Your logout observation and explanation'`. A failed or inconclusive result is valid to report; explain what you could and could not establish.

If it stopped, record that result and ask the instructor about the account's logout settings. Enabling a service arranges startup with the user manager; it does not decide whether that manager stays running after logout. Do not change machine settings yourself. Start your service again if needed, then return to [requests and logs](#5-follow-real-requests).

## Troubleshooting

Use this reference after reading the error, or ask the guide for a hint.

| Observation | What to inspect |
| --- | --- |
| Unit not found | Check the filename under `~/.config/systemd/user/`, then run `daemon-reload`. |
| `203/EXEC` | Check whether the executable named by `ExecStart` exists and can run. |
| Unknown flag | Caddy started but rejected an argument. Read its journal message; unit verification does not check Caddy's options. |
| Failed at step CHDIR | Check `WorkingDirectory` and directory access. Do not broaden permissions to hide the problem. |
| Address already in use | Stop your manual Caddy with `Ctrl-C` in its terminal. Do not change ports or kill unknown processes. |
| Start request repeated too quickly | Fix the original error, then clear the limit with `reset-failed` and restart. |
| Active, but `404` or the wrong page | Compare `--root` with the published directory and its index. `200` can still deliver the wrong content. Do not enable directory browsing to hide a missing page. |
| Published output missing | Check that source remains in `~/src`, then run `build-website`. Restarting Caddy cannot recreate files. |
| Local page works, public page fails | Bring the local result and public error to the instructor. Do not change shared routing or bypass TLS checks. |

## References

- [systemd-analyze](../../commands/systemd-analyze.md), [systemctl](../../commands/systemctl.md), and [journalctl](../../commands/journalctl.md).
- [Watch service logs](../../quests/watch-service-logs.md) for another request experiment.

## Next Session

S9: **2026-10-10**, Automate It. Hand It Over. Bring your working service, source copy, and questions.
