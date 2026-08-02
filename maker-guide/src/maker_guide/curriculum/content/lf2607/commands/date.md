# Command: `date`

Print the system date and time.

```bash
date
date -u
date '+%Y-%m-%d %H:%M:%S %Z'
date --debug +%F
```

Use it when you need the machine's idea of now. Use `date -u` when you need UTC.

## How To Read It

The output includes a date, time, and timezone abbreviation. Logs, HTTP headers, cron, systemd timers, and git commits can use different timezone assumptions. For this course, course dates are local to `Asia/Singapore`.

GNU `date --debug +%F` prints an ISO date to stdout and an output-format diagnostic to stderr, then exits zero. stderr can carry diagnostics even when a command succeeds; the exit status reports success or failure.

## Common Failures

- Time looks wrong: compare `date` and `date -u` before assuming the server clock is wrong.
- Scheduled work ran at a surprising time: check the timezone used by cron or systemd.
- HTTP `Date` header differs from local time: HTTP dates are commonly GMT.

## Docs Pointers

- Run `man date`, then read `-u` and format examples.
- Read [Time Zones](../concepts/time-zones.md).
