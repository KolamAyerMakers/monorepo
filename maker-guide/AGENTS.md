# Agent Notes

<!-- ponytail: this is the smallest useful handoff for the Python bot. -->

## Project

- `maker-guide` is a Python 3.13 learner support and teaching automation bot.
- SQLite is the source of truth. `/makers`, Unix groups, and JSONL files are projections or audit artifacts.
- Application database code uses `sqlite3`. Alembic is only migration plumbing; migrations are hand-written raw SQL.
- Curriculum content lives as typed frozen Python dataclasses under `src/maker_guide/curriculum`, not TOML or YAML.

## Validation

- Never run checks before committing. Commit completed changes and trust Lefthook's pre-commit gate; fix and recommit only when that gate fails.
- When adding a project, package, or other independently validated component, add its checks to Lefthook in the same change.

## Test Policy

- Do not add a test merely because code changed. Add the smallest test only when it protects a realistic domain regression not already covered by the existing suite.
- Do not test trivial wiring, constants, pass-through behavior, exact wording, or implementation details. A bug-fix test must fail before the fix; an existing broader test that demonstrates the failure is sufficient.
- Prioritize tests for security, authorization, persistence, transactions, migrations, recovery, data-loss risks, and documented curriculum invariants. Prefer extending an existing test over creating a new test file.
- Writing no new test is the correct default for changes without meaningful behavioral risk.

## Deployment Artifacts

- Build the relocatable venv tarball with `make venv-artifact`.
- `maker-guide` is tightly coupled to its Salt deployment. Before changing CLI names, installed paths, config shape, socket behavior, learner creation, Unix groups, `/makers` or `/docs` projections, systemd behavior, venv packaging, shell hooks, or privileged helper flows, inspect and update `../infra/salt/states/roles/kam-classroom` and `../infra/salt/pillar/roles/kam-classroom`.
- Deployment installs immutable venv releases under `/usr/local/lib/maker-guide/releases` and atomically updates `/usr/local/lib/maker-guide/current`. `/usr/local/bin/maker-guide-*` symlinks target `current/bin/<command>`.
- Salt owns `/etc/maker-guide/config.toml`, `/var/lib/maker-guide`, `/run/maker-guide/preexec.sock`, `/makers`, `/docs`, `maker-guide-bot.service`, `maker-guide-sync-derived-data.service`, the sync timer, registration sudoers, and the global Bash hook.

## Safety

- Do not make the daemon root. Privileged group changes go through the narrow helper commands and sudoers policy.
- Do not trust identity fields sent by shell hooks; use kernel peer credentials for local socket callers.
- Do not use JSONL audit files to rebuild SQLite.
