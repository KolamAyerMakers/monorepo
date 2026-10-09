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

The released starter validates Open-Meteo forecast data and CAMS modelled PM2.5, then leaves jq extraction and Markdown composition for you to complete before atomic replacement. Forecast maximum temperature is not current temperature; CAMS is neither official PSI nor a local station. Its page distinguishes forecast date, air-model timestamp, retrieval time, units, and sources. A failed update preserves the previous page and prevents the build.

Use [S9 self-study](self-study.md) for the incomplete starter and exercise, service, timer, and short-timer proof. Restore both hourly settings afterward.

## Before S10

S10 is **2026-10-24: Show What You Can Do**. No preparation is required.
