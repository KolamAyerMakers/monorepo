# S10 Recap: Show What You Can Do

Session: S10

2026-10-24

## What You Practiced

- A 20-minute unfamiliar investigation: state a question, inspect, try a safe test, record evidence and the next test. Bandit was one optional choice, with no level or rank requirement.
- A five-minute demonstration of work you chose, supported by real evidence and a real recovery explanation.
- One next action and a date, kept somewhere you will use it. Publishing is optional when it is not meaningful.

The three-hour session protected 75 minutes for twelve five-minute demos and transitions. The focus was choosing evidence and explaining your work.

## Evidence Over Claims

A timer listing proves a schedule exists, not that new facts were published. An active service does not prove a public page is reachable. A local commit does not prove the source was pushed.

Choose evidence that supports your actual claim: changed public content, successful body comparisons, request logs, a peer's successful use of the README, or the files visible in Forgejo. If a result failed, explain that result rather than substituting expected output.

Explain recovery as symptom, observation, cause, repair, and confirming evidence. Do not invent a success story or break a live service merely to make the demonstration dramatic.

## Preserve Useful Work

Keep site source and the operations README in `~/src`. Preserve `scripts/maker-report.sh`, `scripts/site-check.sh`, `services/site.service`, `services/site-build.service`, and `services/site-build.timer` in the pushed repository. Active scripts remain in `~/scripts`; active units remain in `~/.config/systemd/user`.

Use the [source handoff and restoration instructions](../../quests/prepare-source-handoff.md), keeping the serving unit aligned with the [S8 Caddy unit](../S08/self-study.md#2-create-the-user-unit). Personal Caddy uses `WorkingDirectory=%h`, an explicit `--root %h/public_html`, and `--access-log`; shared Caddy handles public HTTPS and forwards to the personal process over loopback HTTP. Same software, two processes. Use `systemctl --user` for your service, never `caddy stop` or `caddy reload`, which can target shared Caddy's admin endpoint.

The timer's service refreshes report Markdown first, then builds; npm alone does not collect facts. Failed collection must preserve the last valid report and prevent the build.

## Carry Out The Next Action

On your chosen date, do the action and record what happened. A calendar or private note is sufficient; a public page is useful only if you want an audience. No particular heading or exact wording is required.

If earlier work is incomplete, name the gap and agree on a dated recovery action. Show what actually works without turning an unfinished item into a false success claim.

Use [S10 self-study](self-study.md) for optional Bandit connection steps, demo evidence commands, recovery pointers, and next-action examples.
