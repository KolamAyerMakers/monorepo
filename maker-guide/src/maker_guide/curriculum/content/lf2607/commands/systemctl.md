# systemctl --user

## Use

First create the standalone `sample-web.service` and test page from [systemd user services](../concepts/systemd-user-services.md). Use your own unit name when operating a different service.

```bash
systemctl --user status sample-web.service
```

## What It Does

`systemctl --user` manages services owned by your user account.

## Lifecycle

```bash
systemctl --user daemon-reload
systemctl --user enable --now sample-web.service
systemctl --user status sample-web.service
systemctl --user restart sample-web.service
systemctl --user stop sample-web.service
systemctl --user disable sample-web.service
```

`daemon-reload` makes systemd re-read unit files after edits; restart the service to apply them to its process. `enable --now` enables future starts and starts immediately, but does not restart an already running service. `stop` ends the current run; `disable` removes enablement. Neither an active state nor a successful restart proves the HTTP content works: repeat the request from the setup card.

## Recovery Table

| Symptom | Likely Cause | Fix |
|---|---|---|
| `Unit sample-web.service not found` | Wrong file path or no daemon reload | Confirm `~/.config/systemd/user/sample-web.service`, then run `daemon-reload`. |
| `Failed at step EXEC` | Bad executable path in `ExecStart` | Use `command -v caddy` and update the unit. |
| `Address already in use` | Another process owns the port | Inspect listeners. Stop only your own identified practice process with consent to interrupt it, or choose another unused port for the standalone sample. Never kill an unknown process or change an assigned production port. |
| Command asks about system service | Missing `--user` | Re-run with `systemctl --user ...`. |

## Watch Out

Do not omit `--user` when managing your account's services. Enablement is separate from [lingering](../concepts/lingering.md) and does not guarantee the user manager survives logout.

## Docs Pointers

- Run `man systemctl`.
- Read [systemctl manual](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html).
- Read [systemd user services](../concepts/systemd-user-services.md), [service](../concepts/service.md), [journalctl](journalctl.md), and [systemd timer](systemd-timer.md).
