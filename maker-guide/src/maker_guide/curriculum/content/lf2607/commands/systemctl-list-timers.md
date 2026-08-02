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

No listed timer means systemd does not know about it yet or it is disabled. Run `systemctl --user daemon-reload`, then `systemctl --user enable --now site-build.timer`.

## Docs Pointers

- Run `man systemctl`.
- Read [systemd timer](systemd-timer.md), [systemctl](systemctl.md), and [automation timers](../concepts/automation-timers.md).
