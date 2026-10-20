# S8 — Keep Your Server Running

Let systemd manage your server, read its journal, and repair failures from evidence.

**You need:** the working S7 site and a systemd user manager. Use your classroom shell or the Ubuntu environment in [Continue at Home](../../guides/continue-at-home.md). Stop any manual Caddy or preview with `Ctrl-C` first.

## 1. Meet the manager

Linux's kernel starts PID 1 during boot. On this machine, that is **systemd**, which brings up and manages services:

```bash
ps -p 1
```

The **system manager** handles machine-wide services. Your separate **user manager** handles your account's services; `systemctl --user` talks to it. No `sudo` is needed for these exercises.

A **unit file** contains the manager's instructions. A service unit ends in `.service`.

## 2. Create the unit

In class, print your assigned port:

```bash
printf '%s\n' "$((10000 + $(id -u)))"
```

If above `65535`, ask the instructor. At home use `8080`.

```bash
mkdir -p ~/.config/systemd/user
micro ~/.config/systemd/user/site.service
```

Read an existing unit before changing it; do not overwrite instructions for another application. Save this example, replacing `12345` with your classroom port:

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

**At home**, use `--listen 127.0.0.1:8080` instead of `:12345`, so the site is local-only.

- `ExecStart` is the command; `%h` is your home directory. This is **not Bash**: do not use `$PORT` or shell arithmetic here.
- `WorkingDirectory=%h` stays stable while publication replaces `public_html`. The explicit `--root` selects the current published tree.
- `Restart=on-failure` retries a failed process, not a deliberate stop.
- `WantedBy=default.target` lets enabling attach the service to your user manager's normal startup target. Merely writing it starts nothing.

Keep credentials and private symlinks out of the published root. Shared Caddy handles classroom HTTPS; do not add `--domain` or change shared configuration.

## 3. Verify, load, start

```bash
systemd-analyze --user verify ~/.config/systemd/user/site.service
```

Fix verification errors and investigate warnings before starting. Verification checks unit settings and executable availability, **not** Caddy's flags or your page. Then:

```bash
systemctl --user daemon-reload
systemctl --user start site.service
systemctl --user enable site.service
systemctl --user status site.service
```

`daemon-reload` reads saved instructions. `start` runs now. `enable` arranges startup with the user manager. Look for `active (running)`; `q` leaves the status pager.

In class, request the local page and public service route:

```bash
curl -i --max-time 10 "http://127.0.0.1:$((10000 + $(id -u)))/"
curl -I --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
```

At home, use `curl -i --max-time 10 http://127.0.0.1:8080/` instead. Inspect the page in your browser too. A running process or `200` alone can still serve the wrong content.

After changing a running unit, use `daemon-reload` **and** `restart`; reloading instructions does not replace the running process.

## 4. Read real requests

```bash
journalctl --user -u site.service --since "5 minutes ago"
journalctl --user -u site.service -f
```

The **journal** stores service messages. `-f` follows new ones. While following, visit the homepage and an absent path from your browser. Find their method, URI, status, and time (`ts` in JSON).

`404` means the server answered a missing-resource request, not that the service failed. In class, the direct client address may be the loopback proxy, not the visitor.

Press `Ctrl-C` to stop following, then reload the homepage. You stopped `journalctl`, not Caddy.

Try `systemctl --user stop site.service`, observe the missing service, then `systemctl --user start site.service`. An intentional stop stays stopped despite `Restart=on-failure`.

## 5. Publish and preserve

Edit existing source under `~/src/pages`, then build. Use `build-website` in class or `cd ~/src && node scripts/build.mjs` at home. Reload and find your change **without restarting the service**.

Keep a copy of the working unit outside `pages`:

```bash
mkdir -p ~/src/services
cp -i ~/.config/systemd/user/site.service ~/src/services/site.service
```

Inspect an existing copy before replacing it. Use S4's deliberate Git workflow to commit only the intended file. The source copy is not installed: editing it alone changes no running service.

<a id="7-break-and-read-the-error"></a>

## 6. Practise diagnosis

**In class:** `guide now` starts one of five service mysteries. It changes your service or published output, not your source or another learner's site. Repeated calls inspect the open challenge. Use `guide` for a hint and `guide answer 'cause and repair'` to explain your recovery.

**At home:** try the five manual experiments in [Worked Answers — S8](../../guides/self-study-answers.md#s8-systemd). Each includes a way back. Read only the experiment first, predict, then diagnose before looking at the explanation. Make one fault at a time.

Use the same evidence in either environment:

```bash
systemctl --user cat site.service
systemctl --user status site.service
journalctl --user -u site.service --since "5 minutes ago"
systemd-analyze --user verify ~/.config/systemd/user/site.service
```

Also request your local page with curl. Did launching fail, did connecting fail, or did the server return the wrong content? Find the original error, not just a later retry-limit message.

<a id="8-restore-and-recover"></a>

## 7. Repair and verify

Make the smallest repair that explains the evidence. For unit changes, edit the installed file, verify it, then:

```bash
systemctl --user daemon-reload
systemctl --user restart site.service
```

If retries hit the start limit, fix the cause first, run `systemctl --user reset-failed site.service`, then restart. Clearing the limit is not a repair.

For missing publication, inspect source and rebuild instead. Recovery means your correct page is back in curl **and** the browser. Explain the cause and why the repair worked; refresh the source copy after a lasting change.

<a id="9-test-logout-survival"></a>

## 8. Classroom extension: test logout

Record the service's `Main PID` and activation time from `status`. Close **all** SSH connections, refresh the service page before reconnecting, then compare status after reconnecting.

A working page while away, with both values unchanged afterward, supports continuous operation during the test. `active` after reconnecting alone could hide a restart.

If it stopped, record that outcome and ask about account logout settings. Enabling a service does not keep the user manager alive. [Lingering](../../concepts/lingering.md) explains the distinction.

**At home:** closing a terminal is not a machine shutdown. A VM or WSL instance can stop when its host stops it; no user service can keep running without its Linux environment. Leave logout/boot policy as a separate experiment.

## Check yourself

- Distinguish `verify`, `daemon-reload`, `start`, `restart`, and `enable`.
- Explain why `Ctrl-C` on `journalctl -f` leaves the server running.
- Explain why a missing HTML file needs a build, not a service restart.
- For a failure you repaired, name the evidence, cause, and successful page check.

[Answers](../../guides/self-study-answers.md#s8-systemd). References: [systemctl](../../commands/systemctl.md), [journalctl](../../commands/journalctl.md), and [systemd-analyze](../../commands/systemd-analyze.md).

## Troubleshooting

| Observation | Inspect first |
|---|---|
| Unit not found | Filename and directory; reload saved units. |
| `203/EXEC` | Executable path and whether it can run. |
| Unknown Caddy flag | Journal: systemd launched Caddy, but Caddy rejected an option. |
| Failed at step CHDIR | `WorkingDirectory` and directory access. |
| Address already in use | Your manual server or preview; identify it before stopping it. |
| Start request repeated too quickly | Earlier error; repair before `reset-failed`. |
| Active, wrong page or `404` | Root, published index, and source—not just process state. |
| Local works, public fails | Classroom routing/TLS evidence; do not change shared settings. |
