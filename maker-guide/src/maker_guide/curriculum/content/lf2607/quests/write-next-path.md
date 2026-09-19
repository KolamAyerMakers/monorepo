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

If the service is `activating`, wait for it to finish and inspect again. Do not stop it mid-publication. Let any terminal build finish too, and leave the timer stopped through the build and Git review so report source cannot change underneath the commit. If these units were never created, name that unfinished work rather than making empty files.

Open `micro ~/src/pages/next.md` and keep useful existing content. Adapt the example to your plan; save with `Ctrl-S` and quit with `Ctrl-Q`. Add a link in the existing homepage source without replacing other content:

```markdown
[What I will try next](next.html)
```

## Optional Publish Workflow

Inspect the new page in your editor too: Git diff does not show untracked contents. Run one command at a time and stop on a failed build or request:

```bash
build-website
curl --max-time 10 -fsS "https://lf2607.kolamayermakers.org/~$USER/next.html"
cd ~/src
git status
git diff -- pages/next.md pages/index.md
git diff --cached
git add -- pages/next.md pages/index.md
git diff --cached
git status
git commit -m "Record my next project step"
git remote -v
git push
git log --oneline -3
git status
```

Here the interactive `build-website` alias publishes the page; it does not collect new report facts. The timer is paused so it cannot race this standalone build. If unrelated files are already staged, stop before adding or committing and resolve the selection with their owner. Inspect and stage any other intended source change separately by its explicit path; do not use broad staging or commit secrets. Use the [S4 Git and Forgejo workflow](../sessions/S04/self-study.md#git-workflow) if the repository or remote is missing, not a second project. Do not force-push a rejected update.

Open the homepage link and new page from your laptop and verify the actual content, then verify the commit and page source in Forgejo. A local commit alone is not off-machine publication.

Restore the existing reviewed hourly timer after finishing, even if there was nothing new to commit:

```bash
systemctl --user start site-build.timer
systemctl --user list-timers --all site-build.timer
```

If it still has the short classroom schedule, use [Hourly Schedule](../sessions/S09/self-study.md#hourly-schedule) to replace the old directives, reload while stopped, and start it. If report safety or another failure makes automation unsafe, leave it stopped and record the blocker with staff instead.

## On The Chosen Date

Do the action, record what happened, and choose the next small step from that evidence. Update the public page only if you chose to share the plan; a private note or calendar remains a complete outcome.

## Related Reading

- [Multi-page sites](../concepts/multi-page-sites.md)
- [README writing](../concepts/readme-writing.md)
