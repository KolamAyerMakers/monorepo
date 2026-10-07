# S9 Recap: Give Your Website a Daily Update

Session: S9

2026-10-10

## Remember

- A service says **what** work to do; a timer says **when** to start it.
- `site-build.service` is a finite oneshot build. `site.service` remains the always-running web server.
- `OnCalendar=*-*-* 09:00:00` schedules a daily build in the server's local time zone. Calendar timers are approximate.
- `systemctl --user list-timers` shows a deadline; the service journal shows whether the work succeeded.
- A build renders existing source. Run your content generator before it when you want a fresh daily page.

## Your Daily Pick

The challenge generates a seven-choice weekly rotation into `~/src/pages/today.md`, links it from the homepage, and publishes `/today.html` on each build. Customize the picks to make the page yours. It is generated static content, not browser-side automation.

Use [S9 self-study](self-study.md) for the complete service, timer, and challenge instructions. Restore the daily 09:00 schedule after a short timer experiment.

## Before S10

S10 is **2026-10-24: Show What You Can Do**. No preparation is required.
