# Lingering

## Core Idea

Lingering controls whether user-managed services may keep running after logout.

On the shared course server, this is infrastructure policy. Learners should understand the idea, but they do not run `loginctl enable-linger` themselves.

## Practice Alone

Check service behavior after logout and understand who enables lingering on the shared server.

```bash
loginctl show-user "$USER" -p Linger
systemctl --user status site.service
```

`Linger=yes` means your user service manager can keep running after you log out. `Linger=no` means logout may stop user services unless staff changes the course server setting.

## Done When

You know why a service can survive your SSH session ending.

## Docs Pointers

- Read [systemd user services](systemd-user-services.md), [service](service.md), and [processes](process.md).
