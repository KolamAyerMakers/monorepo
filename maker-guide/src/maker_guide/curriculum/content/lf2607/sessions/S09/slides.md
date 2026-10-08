# Give Your Website a Daily Update

Session: S9

2026-10-10

Your website can update itself while you are away.

<!-- end_slide -->

# A Timer Is A When, Not A What

A systemd **service** describes a task. A **timer** tells systemd when to start that service.

The task runs, finishes, and waits for its next scheduled start. No loop needs to stay running.

<!-- end_slide -->

# Finite Work Beside An Always-On Server

- `site.service` keeps serving the current website.
- `site-build.service` builds the site once, then exits.
- `site-build.timer` starts that build service on a schedule.

The web server keeps serving the site while the build runs.

<!-- end_slide -->

# More Than "Run Every Day"

- Run every morning or every Monday.
- Run five minutes after the timer is activated.
- Wait ten minutes after the job finishes before running again.
- With persistent calendar timers, catch up once when reactivated, not once for each missed run.

<!-- end_slide -->

# First, Build The Site Once

Save as `~/.config/systemd/user/site-build.service`:

```ini
[Unit]
Description=Build my website

[Service]
Type=oneshot
WorkingDirectory=%h/src
ExecStart=/usr/local/bin/maker-guide-build-personal-website
```

`Type=oneshot` means systemd waits for this finite task to finish.

```bash
systemctl --user daemon-reload
systemctl --user start site-build.service
journalctl --user -u site-build.service
```

Check the journal for a successful build. A completed oneshot normally shows inactive; that is expected.

<!-- end_slide -->

# Now Say When: Every Morning

Save as `~/.config/systemd/user/site-build.timer`:

```ini
[Unit]
Description=Build my website every morning

[Timer]
OnCalendar=*-*-* 09:00:00

[Install]
WantedBy=timers.target
```

The matching name makes this timer start `site-build.service`.

<!-- end_slide -->

# Read The Calendar

`OnCalendar=*-*-* 09:00:00` means every day at 09:00 in the server's local time zone. Without a time, a calendar event defaults to midnight.

Calendar timers are approximate, not a real-time promise. Ask systemd to explain the next occurrence:

```bash
systemd-analyze calendar '*-*-* 09:00:00'
```

Example: Saturday 10 October 2026, 13:00 (+08).

Illustrative output at that time:

```text
$ systemd-analyze calendar '*-*-* 09:00:00'
Normalized form: *-*-* 09:00:00
    Next elapse: Sun 2026-10-11 09:00:00 +08
       (in UTC): Sun 2026-10-11 01:00:00 UTC
       From now: 20h left
```

<!-- end_slide -->

# Make The Daily Schedule Active

```bash
systemctl --user enable --now site-build.timer
systemctl --user list-timers --all site-build.timer
```

The timer listing shows the next scheduled time, not proof a build succeeded. The journal shows what happened. A user timer also depends on the user manager being available.

<!-- end_slide -->

# Make A Daily Pick

The service currently builds unchanged source. To publish changing content, a generator must update source before each build: systemd runs `ExecStartPre` before `ExecStart`.

Create `~/scripts/todays-pick.sh`: choose one short personal recommendation, joke, song, or challenge for today, write it to `~/src/pages/today.md`, and link it from your homepage. Add the generator as `ExecStartPre=/bin/bash %h/scripts/todays-pick.sh` in `[Service]` before the build command; the installed build helper builds the site afterward.

Now each daily build can publish your pick. A scheduled update is static content generated on the server—not a page that magically changes in a visitor's browser.

<!-- end_slide -->

# Your Challenge: A Week Of Picks

Make a seven-choice weekday rotation that fits your site. Add the generator before the build in the service, then verify that the newly generated pick appears on your published `/today.html` page after a run. For the timer proof, follow [the self-study challenge instructions](self-study.md#challenge-a-rotating-daily-pick). Restore the daily schedule afterward.

Make it yours: a mini drawing prompt, five-minute game, local discovery, or something only your site would recommend. Restore the 09:00 daily schedule when finished.
