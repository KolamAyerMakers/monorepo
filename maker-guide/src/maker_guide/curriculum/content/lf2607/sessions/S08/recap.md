# S8 Recap: Keep Your Server Running

Session: S8

Date: 2026-09-26

## What Changed

In S7, Caddy ran in an open terminal. In S8, **systemd** took over: a **unit file** describes the service, and your **user manager** runs it independently of your terminal.

During startup, the kernel starts **PID 1**, which fills the **init** role of bringing up the rest of the system. On our machine, this is systemd's system manager. Your user manager is a separate process; `systemctl --user` talks to it, not PID 1.

Shared Caddy still handles public HTTPS and forwards to your Caddy. The static route serves files independently, so it does not test your service.

## Remember The Unit

The installed unit is `~/.config/systemd/user/site.service`. Keep a working source copy at `~/src/services/site.service`, outside published pages. See the [complete unit and preservation steps](self-study.md#2-create-the-user-unit).

- `ExecStart` names the command. Use your actual numeric port, not a shell calculation.
- `%h` means your home directory. Keep `WorkingDirectory=%h` and explicit `--root %h/public_html` so Caddy reads the current published files.
- `Restart=on-failure` retries failures, not intentional stops.
- `WantedBy=default.target` lets `enable` arrange startup with your user manager; it does not start the service by itself.

Keep private files and symlinks to them out of the published root. Use `systemctl --user`, never `caddy stop` or `caddy reload`, which can target shared Caddy. No `sudo` or shared configuration changes are needed.

## Choose The Right Action

| Task | Command |
| --- | --- |
| Check a unit without starting it | `systemd-analyze --user verify ~/.config/systemd/user/site.service` |
| Reread saved units | `systemctl --user daemon-reload` |
| Start now | `systemctl --user start site.service` |
| Arrange automatic startup | `systemctl --user enable site.service` |
| Stop deliberately | `systemctl --user stop site.service` |
| Apply an edited unit | Verify it, run `daemon-reload`, then `systemctl --user restart site.service` |
| Publish source changes or recreate missing output | `build-website`, then reload the browser, without restarting Caddy |
| Read service state | `systemctl --user status site.service` |
| Read recent messages | `journalctl --user -u site.service --since "5 minutes ago"` |
| Follow new messages | `journalctl --user -u site.service -f` |

Press `q` to leave a paged view. `Ctrl-C` stops the journal follower, not Caddy. Match requests by time, `request.method`, `request.uri`, and `status`.

## Check The Actual Page

An active unit does not prove your site works; HTTP `200` can deliver the wrong page. Read the local response and open your service homepage in the laptop browser:

```bash
curl -i "http://127.0.0.1:$((10000 + $(id -u)))/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
```

## Diagnose, Repair, Explain

The five mysteries use `guide now` to launch each challenge once. Later calls inspect it without breaking it again. The guide changes your service or published files, never your source in `~/src`. Ask it a question for one hint based on fresh diagnostics.

Read the unit, state, recent journal, and local response before editing. Make the smallest repair that explains them. After a unit edit, verify, reload, and restart. If retries reached the start limit, use `reset-failed` before restarting; it clears the limit, not the cause. Missing published output needs a build from source, not a service restart.

Each challenge needs your working local page and one short sentence explaining the cause and why the repair worked. Answer with `guide answer 'Your explanation'` or in the interactive guide. There is no skip. Leave the site working and [preserve the repaired unit](self-study.md#4-preserve-the-working-unit).

## Did It Survive Logout?

Use `systemctl --user status site.service` before and after closing all SSH connections. Keep `Main PID` and the date and time after `since` on the `Active:` line. Refresh the public service page while logged out, before reconnecting.

If the PID or activation time changed, Caddy restarted. A working page while logged out and unchanged values support continued operation during that test. `active` after login alone is not enough. If it stopped, report that and ask the instructor about logout settings; enabling a unit does not set those policies.

## Next Session

S9: **2026-10-10**, Automate It. Hand It Over. Bring your working service, source copy, and questions. Use the [self-study guide](self-study.md) for procedures and troubleshooting.
