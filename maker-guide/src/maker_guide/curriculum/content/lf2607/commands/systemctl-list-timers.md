# systemctl --user list-timers

## Use

```bash
systemctl --user list-timers
```

## What It Does

This lists scheduled timers for your user account.

## What To Read

- `NEXT`: when systemd expects to run it next.
- `LEFT`: approximate time until then.
- `UNIT`: the timer unit.
- `ACTIVATES`: the service the timer starts.

## Watch Out

The default list shows active timers, not every installed timer. Use `systemctl --user list-timers --all` and `systemctl --user list-unit-files --type=timer` to distinguish inactive from missing units. For a runnable example, follow the [systemd timer card](systemd-timer.md); do not enable an unrelated timer merely because the list is empty.

## Docs Pointers

- Run `man systemctl`.
- Read [systemd timer](systemd-timer.md), [systemctl](systemctl.md), and [automation timers](../concepts/automation-timers.md).
