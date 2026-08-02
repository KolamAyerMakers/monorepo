# Time Zones

## Core Idea

A timestamp is only useful when you know which clock rules produced it. Linux stores and displays time using the system clock, time zone settings, and locale formatting.

## Commands To Try

```bash
date
date -u
```

`date` prints local time. `date -u` prints UTC. Course dates use the course-local timezone `Asia/Singapore`, even if a server, website, or external API displays another timezone.

## Why It Matters

Logs, cron jobs, systemd timers, and git commits all depend on time. When debugging scheduled work, always ask: "Which timezone is this output using?"

## Common Confusions

- `UTC` is not a country timezone; it is a reference clock.
- A date can change at different moments in different timezones.
- Cron and systemd timers use the machine's local time unless configured otherwise.
- Web services may return HTTP `Date` headers in GMT.

## Proof Check

Run `date` and `date -u`. If the hour differs, explain which one is local and which one is UTC.

## Docs Pointers

- Run `man date`, then read format examples and `-u`.
- Run `man timedatectl`.
- Read [IANA time zone database background](https://data.iana.org/time-zones/tz-link.html) if you want to know why timezone names look like `Asia/Singapore`.
