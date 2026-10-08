# Write the next path

Quest: write-next-path

## Mission

Choose one concrete next action and a date after S10. Keep it somewhere you will use it: a calendar, private note, README, or a public page when sharing serves a purpose. Publishing is not required.

## Make It Usable

Write what you will do, when you will do it, and how you will notice the result. For example:

```markdown
# Keep My Site Useful

On 2026-10-31, I will use my README to refresh the report and inspect the public result.

I will record the new report date and improve one unclear instruction.

Reference: [systemd service units](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html).
```

Choose your own action and date. No heading must contain Linux, and no exact `Next action:` label is required. A documentation link is useful when you will actually use it, not a formatting requirement. Private plans and access details should stay private.

## Optional Public Page

If publishing is meaningful, use the existing `~/src/pages/next.md`. Work in your own classroom SSH account, not on Bandit or in a similarly named laptop directory.

Pause automatic publishing and inspect the build state before editing:

```bash
systemctl --user stop site-build.timer
systemctl --user status site-build.service --no-pager
```

If the service is `activating`, wait for it to finish and inspect again. Do not stop it mid-publication. Let any terminal build finish too. If these units were never created, name that unfinished work rather than making empty files.

Open `micro ~/src/pages/next.md` and keep useful existing content. Adapt the example to your plan; save with `Ctrl-S` and quit with `Ctrl-Q`. Add a link in the existing homepage source without replacing other content:

```markdown
[What I will try next](next.html)
```

## Optional Local Preview

The interactive `build-website` alias builds the page locally; it does not fetch fresh forecast data. Pause the timer to avoid racing the standalone build, then preview the page on your site if useful. No publication is required.

Keep the timer stopped while you restore the daily 09:00 schedule:

```bash
systemctl --user stop site-build.timer
systemctl --user status site-build.service --no-pager
```

Open the complete unit with `micro ~/.config/systemd/user/site-build.timer`. Replace `OnActiveSec` with `OnCalendar=*-*-* 09:00:00`, save, and quit. Then:

```bash
systemctl --user daemon-reload
systemctl --user cat site-build.timer
systemctl --user start site-build.timer
systemctl --user list-timers --all site-build.timer
```

If another failure makes automation unsafe, leave it stopped and ask staff for help.

## On The Chosen Date

Do the action, record what happened, and choose the next small step from that evidence. Update the public page only if you chose to share the plan; a private note or calendar remains a complete outcome.

## Related Reading

- [Multi-page sites](../concepts/multi-page-sites.md)
- [README writing](../concepts/readme-writing.md)
