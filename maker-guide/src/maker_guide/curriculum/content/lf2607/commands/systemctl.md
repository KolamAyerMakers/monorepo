# systemctl --user

## Use

```bash
systemctl --user status site.service
```

## What It Does

`systemctl --user` manages services owned by your user account.

## Lifecycle

```bash
systemctl --user daemon-reload
systemctl --user enable --now site.service
systemctl --user status site.service
systemctl --user restart site.service
systemctl --user stop site.service
```

`daemon-reload` makes systemd re-read unit files after edits. `enable --now` enables future starts and starts immediately.

## Recovery Table

| Symptom | Likely Cause | Fix |
|---|---|---|
| `Unit site.service not found` | Wrong file path or no daemon reload | Confirm `~/.config/systemd/user/site.service`, then run `daemon-reload`. |
| `Failed at step EXEC` | Bad executable path in `ExecStart` | Use `command -v python3` and update the unit. |
| `Address already in use` | Another process owns the port | Stop the old process or fix the port. |
| Command asks about system service | Missing `--user` | Re-run with `systemctl --user ...`. |

## Watch Out

Do not omit `--user` in this course. We are managing user services, not system services.

## Docs Pointers

- Run `man systemctl`.
- Read [systemctl manual](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html).
- Read [systemd user services](../concepts/systemd-user-services.md), [service](../concepts/service.md), [journalctl](journalctl.md), and [systemd timer](systemd-timer.md).
