# S9 Recap: Keep Your Website Up To Date

Session: S9

2026-10-10

## Remember

- A service says **what** work to do; a timer says **when** to start it.
- `site-build.service` is a finite oneshot build. `site.service` remains the always-running web server.
- `OnCalendar=hourly` with `RandomizedDelaySec=55min` schedules hourly builds with a randomized start window, not strict concurrency spacing or real-time timing.
- `systemctl --user list-timers` shows a deadline; the service journal shows whether the work succeeded.
- A build renders existing source. `ExecStartPre` runs the weather-and-air generator before the build.

## Singapore Conditions

The starter validates bounded Open-Meteo forecast and CAMS modelled PM2.5 data, then leaves field extraction and Markdown composition for you to complete. Keep the saved JSON snapshots, compare extracted values with their source, and distinguish forecast date, air-model timestamp, and retrieval time. The report includes units and source attribution; a failed update preserves the previous page and prevents the build.

Use [S9 self-study](self-study.md) for the seven artifact steps, starter, service, and hourly timer. A timer listing is configuration evidence, not proof of execution or publication.

## Before S10

S10 is **2026-10-24: Show What You Can Do**. No preparation is required.
