# Lingering

## Core Idea

Lingering controls whether user-managed services may keep running after logout.

With lingering enabled, systemd starts the user manager at boot and keeps it available after the last logout. Enablement of an individual service is a separate setting. On a shared machine, lingering is administrator policy; do not change it for an experiment.

## Practice Alone

On a systemd machine, inspect your setting without changing it:

```bash
loginctl show-user "$USER" -p Linger
```

`Linger=yes` permits the user manager to stay available after logout. `Linger=no` means final-logout behavior depends on login/session policy. To inspect a real service, first create the [sample web service](systemd-user-services.md); do not infer an HTTP response from the lingering setting alone.

Lingering does not keep a laptop, VM, or WSL environment running through sleep or shutdown. If `loginctl` cannot contact logind, resolve the environment setup rather than treating it as a `Linger=no` result.

## Done When

You know why a service can survive your SSH session ending.

## Docs Pointers

- Read [systemd user services](systemd-user-services.md), [service](service.md), and [processes](process.md).
