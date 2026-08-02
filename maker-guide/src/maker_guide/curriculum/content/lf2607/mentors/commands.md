# Mentor Commands

Run these commands on the classroom server as a member of the `mentors` group.

## During A Session

Set the current session before running commands that use it:

```sh
SESSION_ID=S03
```

Show the slides:

```sh
presenterm /docs/sessions/$SESSION_ID/slides.md
```

Show progress for the current dated session:

```sh
maker-guide-progress live
```

Show progress for a specific session:

```sh
maker-guide-progress live "$SESSION_ID"
```

Other progress views:

```sh
maker-guide-progress list
maker-guide-progress show <learner-handle>
```

## Release A Session

Release the session to all learners in the course:

```sh
sudo -u maker-guide /usr/local/bin/maker-guide-progress release "$SESSION_ID" --source mentor
```

This is the only privileged release command available to mentors. It runs `maker-guide-progress` as the unprivileged `maker-guide` account, which updates the course release through the application. Do not write to the Maker Guide SQLite database directly.

Sessions must be released in order. Releasing an already released session is safe, but it does not start another documentation build. A new release rebuilds learner documentation automatically.

## Check Services

Check services and timers:

```sh
systemctl status maker-guide-bot.service
systemctl status maker-guide-sync-derived-data.service
systemctl status maker-guide-build-docs.service
systemctl status maker-guide-sync-derived-data.timer
systemctl status maker-guide-build-docs.timer
systemctl list-timers 'maker-guide-*'
```

View the 100 most recent log entries for a service:

```sh
journalctl -u maker-guide-bot.service -n 100 --no-pager
journalctl -u maker-guide-sync-derived-data.service -n 100 --no-pager
journalctl -u maker-guide-build-docs.service -n 100 --no-pager
```

Derived-data synchronization runs every minute. Documentation builds run hourly and after a new session release.

## Documentation Build Recovery

If published documentation is out of date after a release, check the build status and journal above. Mentors cannot start the build service directly. An administrator can recover it with:

```sh
sudo -u maker-guide /usr/bin/sudo -n /usr/bin/systemctl start maker-guide-build-docs.service
```

Do not start, stop, or restart `maker-guide-bot.service` or `maker-guide-sync-derived-data.service`; contact an administrator.

## Registration

Open, close, or check SSH learner registration:

```sh
sudo maker-guide-registration open
sudo maker-guide-registration close
sudo maker-guide-registration status
```

Use `status` before changing registration. Close registration when it is not actively supervised.

## Diagnostics

Show database, projection, and pending-work status:

```sh
maker-guide-ops status --config /etc/maker-guide/config.toml
```

Run the full check before reporting an incident:

```sh
maker-guide-ops check --config /etc/maker-guide/config.toml
```

`check` exits nonzero when intervention is required. Do not run migration, manual synchronization, audit-export, or group-modification commands without administrator instructions.

## Calendar

Show the course calendar:

```sh
maker-guide-calendar lf2607
```

Export iCalendar or CSV:

```sh
maker-guide-calendar lf2607 --output ical > lf2607.ics
maker-guide-calendar lf2607 --output csv > lf2607.csv
```
