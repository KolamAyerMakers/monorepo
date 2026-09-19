# S9 Recap: Automate It. Hand It Over.

Session: S9

2026-10-10

## Two Workshops

1. Schedule an automatic report refresh followed by a build. Observe the activation and changed published facts.
2. Have a peer use your operations README, then preserve and push the source handoff.

## Remember

- `site-build.timer` activates `site-build.service`; `site.service` keeps serving the published site.
- `ExecStartPre` runs `maker-report.sh "System Report"` before `npm run build`. A nonzero report exit prevents the build.
- The report script collects facts into `~/src/pages/maker-report.md`; the builder alone only renders existing source.
- The supplied report resource stops on collection errors and publishes from a temporary file, preserving the last valid report on failure. Upgrade older direct-write copies before unattended use, preserving personal changes first.
- The classroom timer starts after 30 seconds and repeats two minutes after completion. Replace that with the [hourly schedule](self-study.md#hourly-schedule) after observing it.
- Stop the timer and wait for any running build before editing source, running a standalone build, or preparing a commit. Reloading units alone does not restart a timer or a running web server.

## Evidence That Matters

A timer listing is not proof of execution. Match the successful service journal entry with a new date in the generated and publicly fetched report. Keep the actual error if it fails.

A README is tested when another person can use it. The peer reads; the owner operates their own account, restores service, and verifies responses. No credentials change hands.

A local Git log is not an off-machine handoff. Verify the README, source, two scripts, and three units in Forgejo after pushing.

## What To Preserve

Keep `maker-report.sh` and `site-check.sh` active in `~/scripts/`, with copies in `~/src/scripts/`. Keep `site.service`, `site-build.service`, and `site-build.timer` active in `~/.config/systemd/user/`, with copies in `~/src/services/`.

The personal Caddy unit uses `WorkingDirectory=%h` and `ExecStart=/usr/bin/caddy file-server --listen :12345 --root %h/public_html --access-log`, with your assigned numeric port in place of `12345`. The explicit root follows the replaced publication directory. See the [S8 unit](../S08/self-study.md#2-create-the-user-unit) for the complete file and preservation steps.

Shared Caddy handles public HTTPS and forwards to personal Caddy over loopback HTTP. Same software, two processes; do not add `--domain`. Control personal Caddy with `systemctl --user`, never `caddy stop` or `caddy reload`, which can target shared Caddy's admin endpoint.

## Before S10

S10 is **2026-10-24: Show What You Can Do**. Choose evidence for a five-minute demonstration and prepare one real recovery explanation. Name unfinished work honestly rather than presenting expected results as observations.

Use [S9 self-study](self-study.md) for runnable workshop instructions and optional tool pointers. Text tools, another editor, cron, and webring work are not prerequisites.
