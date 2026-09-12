# S9 Recap: Polish And Automation

Session: S9

## Core Idea

The site is now a small system. Systems need automation and documentation.

## Remember

- `site-build.timer` starts the oneshot `site-build.service`; `site.service` keeps serving the site.
- The monotonic timer uses `OnBootSec=5min` and `OnUnitActiveSec=1h`, with no missed calendar-run catchup after downtime.
- A build renders existing report Markdown; rerun `maker-report.sh` separately to collect fresh facts.
- `sed` and `awk` reshape text.
- README files explain projects to other humans.
- The webring makes the cohort visible as a neighborhood.

## Checkpoint Routine

After completing a step, run `guide now`:

- It checks one task and shows the next on success.
- Otherwise, follow the feedback, fix the problem, and try again.

Run `guide now` before starting a quest. Use `guide answer 'your answer'` when asked; `guide check` is an optional explicit check.

## Live Core

Complete these seven steps in order, using the checkpoint routine after each one.

1. Create and enable `site-build.timer`, start its build service, and read a successful build log. Run `guide now`.
2. Run the heading substitution with `sed`. Run `guide now`.
3. Run the first-field extraction with `awk`. Run `guide now`.
4. Create `~/playground/vim-note.txt` with vim and save it with `:wq`. Run `guide now`.
5. Write `~/src/README.md` with build, service, logs, and recovery instructions. Run `guide now`.
6. Enable `webring = true` in `~/src/site.toml` and verify one navigation block after two rebuilds. Run `guide now`.
7. Prepare the source handoff: copy the three working scripts into `~/src/scripts/` and the three units into `~/src/services/`, then commit and push with the README and source changes. Run `guide now`.

Use [Prepare a source handoff](../../quests/prepare-source-handoff.md) for exact paths. Keep the active originals in place; a log of commits alone does not preserve files outside Git.

## Optional Reinforcement

Cron and extra Bandit pipeline practice are optional. If you try cron, remove only your demo job and preserve unrelated entries. Timer creation, text transforms, the vim note, README, webring, and source handoff remain core work.

Run `guide now` for your current session objective; after you complete it, it shows your current quest. Use matching quests for further practice, submit prompted answers with `guide answer 'your answer'`, and use the same checkpoint routine after practice. Optional quests are not graduation prerequisites.

## Can You Explain This?

- Why should temporary cron jobs be removed?
- When would you choose `sed` over opening an editor?
- What should a README tell a stranger?
- What does a systemd timer activate?
- How do you prove the webring navigation is generated idempotently?

## Before S10

S10 is on **2026-10-24**. Rehearse showing your static site and report, the real backend at its local port and public URL, the Forgejo source, and README. Keep one debugging story ready. If you missed earlier work, identify the gap with the instructor and use the relevant self-study guide.

## Full Autonomy

Use [S9 Self-Study Guide: Timers, Text, Polish](self-study.md) for timer creation, explained text transforms, vim save/quit, README and handoff steps, webring verification, and optional cron and Bandit practice.
