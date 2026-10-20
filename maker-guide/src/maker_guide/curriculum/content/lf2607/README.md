# Linux Foundations 2026-07

Follow the session work in class or through the self-study guides. Build, inspect, explain, and improve your own site.

## Start here

Start with the current session below. Slides support the live workshop, self-study gives the practical steps, and the recap helps you revisit what you learned. Your evidence is the work itself: real responses, logs, source changes, recovery, and explanations.

Use the [docs navigation guide](guides/docs-map.md) to move through these files and the [platform reference](guides/platform-reference.md) for hostnames, account paths, public URL shapes, Forgejo conventions, and service ports. The [password guide](guides/passwords.md) covers passphrase rules.

For self-study:

After class, start with [Continue at Home](guides/continue-at-home.md): Ubuntu LTS, a local site, and no classroom account required. Keep [Worked Answers](guides/self-study-answers.md) separate until you have tried the exercises. The practice ZIP supplies starter and complete scripts; the PDF bundle includes the guides and reference cards.

1. Read the session's goals and practical steps.
2. Do the work in your own shell, preserving existing source.
3. Compare actual output with your prediction; inspect the result in a browser when relevant.
4. Diagnose failures, recover safely, and record what you learned.
5. Explain the result in your own words, then compare with the worked answers or recap.

The classroom `guide` command offers help and optional recorded progress. See [Platform Reference](guides/platform-reference.md) and [Scoring](guides/scoring.md). Recorded checks do not replace inspecting your work. When asking for help, include your goal, command, exact error, and what you already tested; remove secrets.


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

### S07: Run Your Own Web Server

Run a foreground Caddy file server, request it locally and publicly, and watch visitor logs. Reuse `ps` and add `ss` to connect your ownership and PID to the listening port. Construct raw HTTP over loopback, change only the path, and compare response status with the log. Diagnose two safe incidents: an empty public practice root and a stopped backend. Restore the real root before comparing local refusal, shared Caddy's `502`, and independent static delivery, then restart. Raw HTTP and the incidents are core; publishing changes, notes, and Git remain optional self-study.

- [Slides](sessions/S07/slides.md)
- [Self-study](sessions/S07/self-study.md)
- [Recap](sessions/S07/recap.md)
- [Reinforcement quests](quests/README.md#s07-reinforcement)
- [Concept cards](concepts/README.md#s07-web-servers-and-diagnostics)

### S08: Keep Your Server Running

Give your web server to a systemd user service. Test it while logged out, follow requests in its journal, and publish without restarting. Then diagnose and repair five guide-launched mysteries, explaining each cause.

- [Slides](sessions/S08/slides.md)
- [Self-study](sessions/S08/self-study.md)
- [Recap](sessions/S08/recap.md)
- [Concept cards](concepts/README.md#s08-services)

### S09: Keep Your Website Up To Date

Learn to inspect JSON weather data, produce a validated Singapore bulletin, and schedule its static-site build with a user timer.

- [Slides](sessions/S09/slides.md)
- [Self-study](sessions/S09/self-study.md)
- [Recap](sessions/S09/recap.md)
- [Concept cards](concepts/README.md#automation)

### S10: This Is Just The Beginning

Keep learning independently: investigate unfamiliar problems with documentation, AI, and community help; choose your next Linux environment; start a small project and improve it through experiments. Use the Julia Evans anthology as a companion, not a reading obligation.

- [Slides](sessions/S10/slides.md)
- [Self-study](sessions/S10/self-study.md)
- [Recap](sessions/S10/recap.md)
- [Reinforcement quests](quests/README.md#s10-reinforcement)
- [Concept cards](concepts/README.md#s10-investigation)

## Reference Cards

- Ordered reinforcement quest index: [quests](quests/README.md).
- Command card index: [commands](commands/README.md).
- Concept card index: [concepts](concepts/README.md).
- Docs navigation rules live in [guides](guides/docs-map.md).
- Learner platform rules live in [guides](guides/platform-reference.md).
- Score, tiers, rankings, and the ledger live in [scoring and rankings](guides/scoring.md).
