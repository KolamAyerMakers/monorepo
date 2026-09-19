# Linux Foundations S9

Session: S9

Automate It. Hand It Over.

2026-10-10

<!-- end_slide -->

# Two Workshops

1. Automatically refresh report facts, then build and prove the published change.
2. Peer-test an operations README and preserve the working source handoff.

Keep the same site, two scripts, and user service. No new helper is needed.

`site.service` runs personal Caddy; shared Caddy still handles public HTTPS. Keep the [S8 unit](../S08/self-study.md#2-create-the-user-unit), including `--root` and `--access-log`, so new publications and request logs remain visible.

<!-- end_slide -->

# Today's Three Hours

| Minutes | Work |
|---|---|
| 0-15 | Inspect the working project and report safety |
| 15-75 | Workshop 1: refresh, build, observe automation |
| 75-85 | Break |
| 85-160 | Workshop 2: README, peer operation, source handoff |
| 160-180 | Verify the handoff and rehearse one explanation |

<!-- end_slide -->

# Workshop 1: Fresh Facts

```text
timer -> report script -> Markdown -> build -> published HTML
```

`maker-report.sh "System Report"` collects new facts.

The builder alone does not regenerate the report.

<!-- end_slide -->

# Failure Must Stop The Chain

A failed report must prevent the build and preserve the last valid report.

Use the current supplied report generator: it collects into a temporary file and replaces the report only on success. Compare older copies and preserve personal changes before updating; the self-study explains the backup and replacement.

Do not work around it by building a partial report.

<!-- end_slide -->

# One Service, In Order

`~/.config/systemd/user/site-build.service`:

```ini
[Unit]
Description=Refresh report and build my site

[Service]
Type=oneshot
WorkingDirectory=%h/src
ExecStartPre=/bin/bash %h/scripts/maker-report.sh "System Report"
ExecStart=/usr/local/bin/npm run build
```

A nonzero pre-start exit prevents `ExecStart`. `build-website` is an interactive alias, not an executable for systemd.

<!-- end_slide -->

# Wait For A Real Activation

Use the [classroom timer and observation sequence](self-study.md#timer-files).

- First activation: 30 seconds after starting the timer.
- Later activations: two minutes after the build service finishes.
- Watch the journal without manually starting another build.
- Compare the old and new report date in the published page.

Timer listings show a schedule, not successful automation.

<!-- end_slide -->

# Leave A Reasonable Schedule

After witnessing the automatic refresh, change to hourly operation.

Stop the timer, let any build finish, replace the short schedule, reload units, then start the timer again. Do not leave both schedules in place.

Use [Hourly Schedule](self-study.md#hourly-schedule). Pause the timer before standalone builds or source handoff work; one systemd unit prevents overlap only for work started through that unit.

<!-- end_slide -->

# Workshop 2: Can A Peer Operate It?

Write an operations README: what runs, where it lives, how to refresh, how to inspect, how to recover.

The peer reads and directs from the README. The owner reviews and runs commands in their own account.

No password swapping. No guessing missing commands aloud: write the missing instruction, then retry.

<!-- end_slide -->

# Test The Instructions

- Find the site's public page and its source.
- Refresh and build through the oneshot service; inspect logs and changed content.
- Agree to a brief stop of the owner's web service, then recover it from the README.
- Confirm the local response and the public service response after recovery.

Swap roles. Record one ambiguity fixed and one observed recovery.

Use `systemctl --user stop site.service` and `systemctl --user start site.service`. Never use `caddy stop` or `caddy reload`; they can target shared Caddy.

<!-- end_slide -->

# Preserve Five Working Files

| Active Files | Source Copies |
|---|---|
| `~/scripts/maker-report.sh`, `~/scripts/site-check.sh` | `~/src/scripts/` |
| `site.service`, `site-build.service`, `site-build.timer` under `~/.config/systemd/user/` | `~/src/services/` |

Copy, do not move. Include README and site source in the existing repository.

Follow [Prepare a source handoff](../../quests/prepare-source-handoff.md): inspect, stage explicit paths, commit, push, verify the actual files in Forgejo.

<!-- end_slide -->

# Exit Evidence

Show an automatic activation in the journal and changed published report facts.

Show the peer-tested README and the pushed two scripts plus three units.

Explain which step collects facts, which builds, and what happens when collection fails.

<!-- end_slide -->

# Help Between Sessions

S10 is **2026-10-24: Show What You Can Do**. Rehearse a five-minute [demo](../../quests/demo-site.md) with evidence you choose and one real recovery story.

Use the [self-study instructions](self-study.md) for recovery. Between sessions, ask the instructor or the guide for help with the command, error, and your next test. Never share secrets.
