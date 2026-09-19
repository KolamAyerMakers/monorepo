# Linux Foundations 2026-07

Follow the session work in class or through the self-study guides. Build, inspect, explain, and improve your own site; use reinforcement quests for extra practice.

## Start here

Start with the current session below. Slides support the live workshop, self-study gives the practical steps, and the recap helps you revisit what you learned. Your evidence is the work itself: real responses, logs, source changes, recovery, and explanations.

Use the [docs navigation guide](guides/docs-map.md) to move through these files and the [platform reference](guides/platform-reference.md) for hostnames, account paths, public URL shapes, Forgejo conventions, and service ports. The [password guide](guides/passwords.md) covers passphrase rules.

For self-study:

1. Read the session's goals and practical steps.
2. Do the work in your own shell, preserving existing source.
3. Compare actual output with your prediction; inspect the result in a browser when relevant.
4. Diagnose failures, recover safely, and record what you learned.
5. Explain the result to a peer or use the recap to review it.

The guide bot is optional learner support, not a required workshop checklist. For help and recorded progress, use the dedicated [IRC support guide](guides/irc-support.md) and [scoring and rankings](guides/scoring.md). Recorded checks do not replace inspecting your live work.

Feeling stuck still counts as progress if you can describe what changed. Post the command you ran, the output you got, and what you expected in `#lf2607`.

## Optional Quest Map

Quests are highly recommended reinforcement. They are not prerequisites for attending the next live session. The [full quest index](quests/README.md) groups them by session.

## Quest Calendar

Quest ids are stable content ids. Availability follows the learner's reached session, not the wall-clock date.

## Sessions

### S01: First contact

First login, shell basics, and your first site build.

- [Slides](sessions/S01/slides.md)
- [Self-study](sessions/S01/self-study.md)
- [Recap](sessions/S01/recap.md)
- [Reinforcement quests](quests/README.md#s01-reinforcement)
- [Concept cards](concepts/README.md#s01-orientation)

### S02: Files and keys

Files, editing, source versus output, and SSH keys.

- [Slides](sessions/S02/slides.md)
- [Self-study](sessions/S02/self-study.md)
- [Recap](sessions/S02/recap.md)
- [Reinforcement quests](quests/README.md#s02-reinforcement)
- [Concept cards](concepts/README.md#s02-files-and-identity)

### S03: Streams, pipes, and processes

Standard streams, redirection grammar, useful pipelines, and process inspection.

- [Slides](sessions/S03/slides.md)
- [Self-study](sessions/S03/self-study.md)
- [Recap](sessions/S03/recap.md)
- [Reinforcement quests](quests/README.md#s03-reinforcement)
- [Concept cards](concepts/README.md#s03-streams-and-processes)

### S04: Permissions, Git, and Forgejo

Permissions, Git, and Forgejo.

- [Slides](sessions/S04/slides.md)
- [Self-study](sessions/S04/self-study.md)
- [Recap](sessions/S04/recap.md)
- [Reinforcement quests](quests/README.md#s04-reinforcement)
- [Concept cards](concepts/README.md#s04-permissions-git-and-forgejo)

### S05: Scripts

Saved commands, direct execution, quoted arguments, and a published report.

- [Slides](sessions/S05/slides.md)
- [Self-study](sessions/S05/self-study.md)
- [Recap](sessions/S05/recap.md)
- [Reinforcement quests](quests/README.md#s05-reinforcement)
- [Concept cards](concepts/README.md#s05-scripting)

### S06: Is your site actually working?

Explore how web requests work, then write a checker that diagnoses your homepage and report page.

Use the [diagnostic cases](sessions/S06/self-study.md#diagnostic-cases) to reason about successful responses, missing pages, and transport failures. Run `bash ~/scripts/site-check.sh "" maker-report.html` against the live site and inspect both pages in a browser. `""` selects home; no arguments must show usage and exit nonzero.

- [Slides](sessions/S06/slides.md)
- [Self-study](sessions/S06/self-study.md)
- [Recap](sessions/S06/recap.md)
- [Reinforcement quests](quests/README.md#s06-reinforcement)
- [Concept cards](concepts/README.md#s06-control-flow-and-networking)
- [Instructor runbook](mentors/S06.md)

### S07: Run Your Own Web Server

Run a foreground Caddy file server, request it locally and publicly, and watch visitor logs. Reuse `ps` and add `ss` to connect your ownership and PID to the listening port. Construct raw HTTP over loopback, change only the path, and compare response status with the log. Diagnose three safe incidents: an occupied own port, an empty public practice root, and a stopped backend. Restore the real root before comparing local refusal, shared Caddy's `502`, and independent static delivery, then restart. Raw HTTP and the incidents are core; publishing changes, notes, and Git remain optional self-study.

- [Slides](sessions/S07/slides.md)
- [Self-study](sessions/S07/self-study.md)
- [Recap](sessions/S07/recap.md)
- [Reinforcement quests](quests/README.md#s07-reinforcement)
- [Concept cards](concepts/README.md#s07-web-servers-and-diagnostics)
- [Instructor delivery notes](mentors/S07-S10.md)

### S08: Keep Your Server Running

Let a systemd user service supervise the backend. Read its journal, safely break and repair your own unit, and investigate logout survival. Tmux and helper functions are optional extensions.

- [Slides](sessions/S08/slides.md)
- [Self-study](sessions/S08/self-study.md)
- [Recap](sessions/S08/recap.md)
- [Reinforcement quests](quests/README.md#s08-reinforcement)
- [Concept cards](concepts/README.md#s08-services)

### S09: Automate It. Hand It Over.

Refresh report facts before building, prove an automatic publication, and peer-test an operations README. Preserve two scripts and three units in a recoverable source handoff; no `site.sh` dispatcher is required. Sed, awk, vim, cron, and the webring are optional.

- [Slides](sessions/S09/slides.md)
- [Self-study](sessions/S09/self-study.md)
- [Recap](sessions/S09/recap.md)
- [Reinforcement quests](quests/README.md#s09-reinforcement)
- [Concept cards](concepts/README.md#s09-automation-and-handoff)

### S10: Show What You Can Do

Lead a demonstration with evidence you choose, investigate an unfamiliar problem, and choose a concrete next step. Explain your actual work in your own words, not a fixed answer script.

- [Slides](sessions/S10/slides.md)
- [Self-study](sessions/S10/self-study.md)
- [Recap](sessions/S10/recap.md)
- [Concept cards](concepts/README.md#s10-investigation)

## Reference Cards

- Ordered quest index: [quests](quests/README.md).
- Command card index: [commands](commands/README.md).
- Concept card index: [concepts](concepts/README.md).
- Docs navigation rules live in [guides](guides/docs-map.md).
- Learner platform rules live in [guides](guides/platform-reference.md).
- Score, tiers, rankings, and the ledger live in [scoring and rankings](guides/scoring.md).
