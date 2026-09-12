# S10 Recap: Graduation

Session: S10

## Core Idea

You now know enough Linux to keep learning without waiting for a class.

## Keep Going

- Keep your site alive.
- Keep working scripts and units copied into the source repo, then commit and push deliberate changes.
- Keep asking public questions.
- Try Bandit again after a week.
- Teach one command to someone else.

## Live Core

- Show the same static site and report, reachable Forgejo repo, working personal service, and useful README.
- Reuse `bash ~/scripts/site-check.sh "" maker-report.html`, then verify the local service port and `"https://$USER.lf2607.kolamayermakers.org/"` from your classroom shell. The static URL is `"https://lf2607.kolamayermakers.org/~$USER/"`.
- Compare fetched report bodies with generated HTML, inspect actual request logs, and open both public URLs in your laptop browser. Service status alone is not end-to-end proof.
- Explain one real debugging recovery and the method recorded in your classroom Bandit notes, without sharing passwords.
- Publish `~/src/pages/next.md` with a Markdown heading containing Linux and an explicit dated `Next action:`. Link, build, commit, and push it.

## Missed-Session Accommodation

If you missed service or handoff work, agree with the instructor on an explicitly reduced demo and a dated recovery plan. Name what is missing.

## Optional Reinforcement

- Try more Bandit levels, a homelab, or a small Linux club project after completing the core demo and next page.
- Extra practice is optional; the S9 timer and source handoff remain part of the project to preserve.
- Use the guide for remaining reinforcement in the classroom: `guide now` shows your current session objective first if one remains; after you complete it, it shows your current quest. Submit prompted answers with `guide answer 'your answer'`, and run `guide check` after practice.

S10 has no new scored session objective. Optional quests are not graduation prerequisites.

## What To Preserve

Keep `~/src/README.md`, site pages, `scripts/maker-report.sh`, `scripts/site-check.sh`, `scripts/site.sh`, `services/site.service`, `services/site-build.service`, and `services/site-build.timer` in the pushed repo. Keep active originals where they run; use the [handoff path table](../../quests/prepare-source-handoff.md#copy-working-files) when restoring them.

Create `~/playground/bandit-notes.md` in the classroom before connecting to Bandit, and keep that SSH tab open. Start Bandit SSH directly from a new laptop terminal tab, not inside the classroom. Switch tabs to keep notes in the classroom, not in a temporary Bandit directory.

Exit Bandit back to your laptop shell, then switch to the existing classroom SSH tab before running site commands. Reconnect from the laptop only if the classroom connection closed, and confirm the classroom machine/account with `hostname` and `whoami` before the demo.

The report generator collects facts. The build and monotonic timer render existing Markdown; they do not collect fresh facts or replay missed calendar runs after downtime.

## Next Steps

Carry out the action and date on your next page, verify its proof, and update the page with what you learned. Keep using documentation, small experiments, and public questions to choose the next step after that.

## Full Autonomy

Use [S10 Self-Study Guide: Boss Fight And Graduation](self-study.md) for Bandit workflow, archive decoding, final demo commands, and the next-step template.
