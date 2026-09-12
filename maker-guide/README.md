# maker-guide

`maker-guide` is a teaching automation and learner support system for Kolam Ayer Makers. It connects IRC, CLI help, shell observations, quest validation, learner progress, LLM tutoring, audit logs, and operational repair commands.

## Security Model

The daemon is designed to run under its own UID and accept events from multiple local users through `/run/maker-guide/preexec.sock`.

Use both controls:

- Filesystem permissions on `/run/maker-guide` and the socket, typically `maker-guide:maker-guide-users 0750` for the directory and `maker-guide:maker-guide-users 0660` for the socket.
- Linux peer credential checks via `SO_PEERCRED`, with allowed users configured by UID and optional group name.

The daemon derives UID and username from kernel peer credentials. It does not trust identity fields sent by shell hooks.

## IRC

IRC SASL authentication is mandatory. The implemented client supports SASL `PLAIN`, requires the server to advertise the `sasl` capability, and refuses to join channels unless authentication succeeds.

## Cohort Releases

Mentors can run `maker-guide-progress release S03` during the in-person session. It releases that session to the whole cohort, triggers `maker-guide-build-docs.service`, and leaves earlier unfinished quests available. The service reads the release from SQLite and atomically publishes release-gated session materials and quests alongside an open reference library. Command cards, concept cards, and general learner guides are available from the start so curious learners can read ahead. Every local document linked from available material must also be available.

## Development Classroom

Curriculum examples use `lf2607.kolamayermakers.org`. When testing on `lf-dev`, replace that hostname with `lf-dev.kolamayermakers.org` in DNS commands, page and service URLs, and the S6 checker's URLs (`base_url` in the reference example). The shared validators accept both classroom hostnames, not arbitrary hosts; the course ID remains `lf2607`.

After deploying a validator update, use `guide now` to check previously recorded successful commands for the current practical objective and show the next task if it passes. `guide check` remains an explicit validation option, or you can rerun the command. Failed commands do not count as completion evidence.

## Example Config

```toml
log_level = "INFO"

[database]
path = "/var/lib/maker-guide/state.db"

[socket]
path = "/run/maker-guide/preexec.sock"
mode = 432
allowed_group = "humans"
queue_size = 1000

[irc]
server = "lf2607.kolamayermakers.org"
port = 6697
tls = true
nickname = "guide"
username = "guide"
realname = "Eto Demerzel"
channels = ["#kolamayermakers", "#lf2607"]

[irc.sasl]
mechanism = "PLAIN"
username = "guide"
password_env = "MAKER_GUIDE_IRC_PASSWORD"

[llm_tutor]
enabled = true
provider = "openrouter"
api_key_file = "/etc/maker-guide/secrets/openrouter-api-key"
max_tokens = 1200

[unix_groups]
enabled = true
grant_command = ["sudo", "-n", "/usr/local/sbin/maker-guide-grant-group"]
revoke_command = ["sudo", "-n", "/usr/local/sbin/maker-guide-revoke-group"]
managed_groups = ["linux-foundations"]
```

TOML integers are decimal, so `432` is octal `0660`.

`llm_tutor.max_tokens` is the OpenRouter generation limit and defaults to `1200`.

Do not put provider secrets directly in the TOML file or commit them to Git. For systemd deployments, store the key in `api_key_file` with permissions readable by the daemon user.

To disable LLM tutoring while keeping deterministic chat commands, omit `[llm_tutor]` or set `enabled = false`.

`maker-guide-sync-groups` reads intended memberships from SQLite `group_grants` and applies drift through configured command arrays. The bot daemon should stay unprivileged. From the kernel and system database point of view, only a privileged process can update group membership. Both the sync command and the privileged helpers enforce `managed_groups`; any SQLite row for another group fails closed before Unix state is read or changed.

Actual mutation flow:

- `maker-guide-sync-groups --apply` runs as the bot user.
- For a missing grant, it runs `grant_command + [handle, group_name]`.
- For a required removal, it runs `revoke_command + [handle, group_name]`.
- The sync command rejects any `group_name` outside `[unix_groups].managed_groups`.
- The helper loads `/etc/maker-guide/config.toml` and enforces the same `managed_groups` allowlist.
- The helper validates both arguments as safe Unix names and rejects administrative groups such as `sudo`, `wheel`, `docker`, `root`, and `adm`.
- The grant helper runs `/usr/sbin/usermod -a -G <group_name> <handle>`.
- The revoke helper runs `/usr/bin/gpasswd -d <handle> <group_name>`.

Those final commands require root. Do not run the whole daemon as root and do not make a Python script setuid. Use direct `sudo -n` command arrays and `sudoers` so only the narrow helper commands can run as root.

Install `/etc/maker-guide/config.toml` root-owned and not writable by the bot user. The helpers read that file for `managed_groups`, so this file is part of the root-side policy boundary:

```sh
chown root:root /etc/maker-guide/config.toml
chmod 0644 /etc/maker-guide/config.toml
```

Allow only the real helper commands through `sudoers` for the bot user:

```sudoers
maker-guide ALL=(root) NOPASSWD: /usr/local/sbin/maker-guide-grant-group *, /usr/local/sbin/maker-guide-revoke-group *
```

The `sudoers` wildcard is not the safety boundary. It only transports privilege. The safety boundary is the helper-side argument validation plus the root-owned `managed_groups` allowlist, and the helper only invokes fixed commands without a shell.

Unix group changes update the system group database. Existing login sessions do not automatically gain or lose supplementary groups; learners need a new login session or an explicit session refresh such as `newgrp` where appropriate.

## CLI

Start the daemon with the configured IRC identity:

```sh
maker-guide-bot --config /etc/maker-guide/config.toml
```

Ask the bot for help from a terminal session:

```sh
guide --config /etc/maker-guide/config.toml
```

Ask one question directly:

```sh
guide --config /etc/maker-guide/config.toml explain chmod 755
```

Use pipeline input:

```sh
make 2>&1 | guide --config /etc/maker-guide/config.toml
```

Chat requests from IRC and `guide` use the same handler. `now` and its `today` and `next` aliases check at most one current practical item: the current released incomplete session objective, or the current quest if it was already assigned. A passing check records completion and displays the next task without validating it or walking a chain of tasks. Incomplete work keeps its current guidance. A newly assigned quest is displayed without checking it, so run `guide now` before starting quest work.

Answer-based and mixed questions still require `answer <your answer>`; `now` does not bypass the answer. `check` and `check my work` remain explicit validation requests. Failed check responses are concise and deterministic. LLM explanations are available only when the learner asks, never automatically after a check.

For the current S6 checker objective or already assigned checker quest, `guide now` and `guide check` automatically request a local simulated test suite. The CLI announces the run and executes `~/scripts/site-check.sh` without arguments as the invoking learner. IRC cannot run it and directs the learner to these commands in the classroom shell. Older CLI clients without this capability cannot complete this check; there is no source-only fallback. Deploy the updated CLI and daemon together.

The reference checker is one implementation, not a required copy. Grading accepts equivalent functions, `case` statements, variable names, page order, and curl flag order. Output must identify each page by URL or homepage/report label, give its HTTP code and diagnosis or a transport-failure diagnosis, and never claim a failed request succeeded. Report-404 advice must name `maker-report.sh` followed by `build-website`; homepage-404 advice must not recommend report regeneration. See the [seven cases and output contract](src/maker_guide/curriculum/content/lf2607/sessions/S06/self-study.md#guide-checks).

A simulated pass is not a live website health check. Learners must still run `bash ~/scripts/site-check.sh` against their real pages and inspect both in a browser. Existing stored completions remain historical records; they are not rerun or reinterpreted as passes of the new suite.

When LLM support is configured, private conceptual answers use a forced tool call to assess each catalog rubric as demonstrated, contradicted, or not demonstrated. Strict application code validates that tool payload and remains solely responsible for progress writes. Provider failures fall back to the deterministic regex checks. Private fallback questions can use the optional LLM tutor with read-only learner context. Public IRC fallback and public answers do not call the LLM because they could expose learner data. The CLI response prompt uses the configured IRC nickname so local terminal conversations match the bot identity seen in IRC. In interactive mode, type `exit` or `quit` to leave.

Mentor identities are initialized with `maker-guide-initialize-learner --no-enroll`. They can use `guide` and receive IRC replies, but have no course membership or learner progress.

Export a curriculum calendar as a table, iCalendar, or CSV:

```sh
maker-guide-calendar lf2607
maker-guide-calendar lf2607 -o ical > lf2607.ics
maker-guide-calendar lf2607 -o csv > lf2607.csv
```

Preview Unix group drift without mutation:

```sh
maker-guide-sync-groups --config /etc/maker-guide/config.toml --dry-run
```

Apply Unix group drift after reviewing the plan:

```sh
maker-guide-sync-groups --config /etc/maker-guide/config.toml --apply
```

The sync command never reads Unix groups as progress. It only projects SQLite `group_grants` into the system group database.

Inspect recovery-relevant operational state:

```sh
maker-guide-ops status --config /etc/maker-guide/config.toml
```

Fail a cron or deployment check when repairable work is backed up:

```sh
maker-guide-ops check --config /etc/maker-guide/config.toml
```

Open or close SSH learner registration:

```sh
sudo maker-guide-registration open
sudo maker-guide-registration close
```

Prune restricted full LLM audit logs after their retention timestamp has passed:

```sh
maker-guide-prune-llm-audit --config /etc/maker-guide/config.toml
```

Prune raw shell command observations after the post-course retention window has passed:

```sh
maker-guide-prune-observations --config /etc/maker-guide/config.toml
```

## Database Migrations

SQLite schema changes are managed with Alembic migrations written as raw SQL. Application code uses `sqlite3`; SQLAlchemy is only isolated Alembic CLI plumbing.

Run migrations through `maker-guide-db`, which reads `[database].path` from the daemon config:

```sh
maker-guide-db --config /etc/maker-guide/config.toml upgrade head
```

Common operations:

```sh
maker-guide-db --config /etc/maker-guide/config.toml current
maker-guide-db history
maker-guide-db --config /etc/maker-guide/config.toml revision -m "create progress tables"
maker-guide-db --config /etc/maker-guide/config.toml upgrade --sql head
maker-guide-db --database /tmp/maker-guide-dev.db upgrade head
maker-guide-db --database /tmp/maker-guide-dev.db downgrade -1
```

Use downgrade only for local development and tests. Production rollback should restore a SQLite backup, then rerun `maker-guide-sync-derived-data` and `maker-guide-sync-groups`.

## Operations And Recovery

SQLite is the recovery source. JSONL audit files are append-only audit artifacts for inspection and reporting; they are not a replay log and must not be used to rebuild SQLite. Audit readers must de-duplicate JSONL rows by `audit_id` because a crash after append but before marking `exported_at` can emit the same audit row again on retry.

`maker-guide-export-audit` takes an `.export.lock` file under the audit root before selecting rows. Treat that lock as the concurrency contract: run at most one exporter per audit root, and investigate a lock contention failure instead of starting another exporter against the same directory.

`maker-guide-sync-derived-data` takes a `.sync.lock` file under the makers root before reading projection state, writing files, or removing stale paths. Treat lock contention as an overlapping sync job and stop the duplicate job instead of deleting files manually while another sync may be active.

Take online SQLite backups with the SQLite shell so the copy is consistent while the daemon may be running:

```sh
sqlite3 /var/lib/maker-guide/state.db ".backup '/var/backups/maker-guide/state.db.backup'"
```

Keep `/var/backups/maker-guide` owned and writable only by trusted operators. Back up `/etc/maker-guide/config.toml` separately because the root-owned Unix group allowlist is part of the privileged policy boundary.

Restore order:

1. Stop the daemon and any scheduled sync/export jobs.
2. Restore the SQLite backup to `/var/lib/maker-guide/state.db` with the expected owner and mode.
3. Inspect migration state with `maker-guide-db --config /etc/maker-guide/config.toml current`.
4. Regenerate learner-visible files with `maker-guide-sync-derived-data --config /etc/maker-guide/config.toml`.
5. Preview Unix group drift with `maker-guide-sync-groups --config /etc/maker-guide/config.toml --dry-run`.
6. Apply reviewed Unix group drift with `maker-guide-sync-groups --config /etc/maker-guide/config.toml --apply`.
7. Export pending audit rows with `maker-guide-export-audit --config /etc/maker-guide/config.toml`.
8. Verify recovery state with `maker-guide-ops check --config /etc/maker-guide/config.toml`.

`maker-guide-ops status` reports SQLite integrity, Alembic revision, unexported audit rows, unsupported validation attempts, outbox backlog grouped by kind and status, and `/makers` projection version. `maker-guide-ops check` exits nonzero when integrity fails, migration state is missing, audit export backlog exceeds the configured threshold, unsupported validation attempts exist, pending or failed outbox rows exist, or the `/makers` projection is missing or stale.

## Classroom Reset

The Salt-managed root command removes either one learner or all classroom runtime data. It is irreversible and requires both `--apply` and an exact confirmation:

```sh
sudo kam-classroom-reset learner alice --apply --confirm alice
sudo kam-classroom-reset all --apply --confirm RESET-LEARNING-ENVIRONMENT
```

The learner scope removes the Forgejo account and repositories, Maker Guide SQLite and JSONL audit entries, LLDAP identity, home directory, `/makers` projection, and Caddy route. It deliberately retains Ergo account and history data. The all scope also removes all learner homes and the LLDAP, Forgejo, Ergo, Authelia, and Maker Guide datastores. It invalidates cached SSSD identities, so learner accounts no longer resolve. It leaves services stopped; reapply the classroom role from the Salt controller to recreate the empty runtime:

```sh
uv run salt-runner ssh-apply lf2607 roles.kam-classroom
```

## Validation Security

Daemon-side deterministic validation runs as the unprivileged bot user. The S6 behavioral suite executes only in the invoking learner's CLI under that learner's UID, never in the daemon. Operators must not run validation as root, add privileged wrappers, or bypass Unix permissions to make a quest pass.

Learner home directories must be traversable by the bot UID, and quest artifacts must be readable through normal Unix permissions. A `permission-denied` validation failure is learner feedback about ownership, directory execute bits, and file read bits. It is not an operator incident to fix with elevated access.

Daemon-side artifact validators inspect only the active catalog paths for the current task. They resolve paths, follow symlinks, inspect file metadata, and read bounded UTF-8 text; the daemon never executes learner files. Regex validators read at most the configured validation byte limit before matching, so large files fail as validation feedback instead of being read without bound.

Relative paths and `~/...` paths are scoped to the learner home after symlink resolution. If a learner-home symlink points outside that home, validation fails with `path-escapes-scope` unless the catalog intentionally declares the exact absolute path.

The Linux-only S6 CLI runner reads at most 1 MiB of source, parses and runs a private, read-only, unlinked temporary source snapshot with Bash via `/proc/self/fd`, uses a sanitized environment and temporary working directory, and bounds each subprocess to three seconds and 64 KiB of combined output within a 25-second suite budget. It rejects root, mismatched real/effective UIDs, and the daemon account. Its PATH-based curl shim delegates option handling to native `/usr/bin/curl` and redirects the two allowed learner URLs on `lf2607` or `lf-dev` to loopback fixtures.

This is not a sandbox. Scripts retain the learner's filesystem and process permissions, can have side effects, and can bypass the PATH shim. Neither URL redirection nor time/output limits isolate untrusted code. Do not run another learner's script, or run the suite as the bot or through sudo. The daemon authenticates the CLI through the existing socket peer credentials, but the local outcome report is not tamper-proof attestation.

Results return on the same authenticated connection and are bound to the selected task, its evidence window, and the source SHA-256. A changed source requires a fresh run; a changed task cannot receive the old result. Raw stdout, stderr, and script source are not sent as result evidence, stored in validation evidence, or passed to the LLM by this flow. Reports carry the digest, fixed case booleans, and a fixed error token; learner feedback uses fixed case messages. See [S6 Behavioral Grading](DESIGN.md#s6-behavioral-grading) for the full trust contract.

## LLM Audit Logs

Private LLM tutoring and conceptual-answer interpretation store full provider requests and raw responses in the restricted `llm_audit_logs` SQLite table. These rows are separate from `quest_attempts`, score progress, validation evidence, and the general JSONL audit export.

Treat the SQLite database as sensitive because `llm_audit_logs` can contain learner messages, curated learner state, and raw model output. Keep `/var/lib/maker-guide/state.db` readable only by the daemon UID and trusted operators. Do not expose this table through learner-facing exports.

Restricted LLM audit rows expire 90 days after creation. Run `maker-guide-prune-llm-audit --config /etc/maker-guide/config.toml` from scheduled maintenance to delete expired rows. Old LLM audit rows are not replayed into future tutor context; future prompts use only the current read-only learner snapshot.

Raw shell command observations are separate learner telemetry. Run `maker-guide-prune-observations --config /etc/maker-guide/config.toml` from scheduled maintenance after the course retention window to delete expired raw observations while keeping durable validation evidence and progress state.

## Deployment Venv

Build the relocatable deployment venv tarball:

```sh
make venv-artifact
```

The generated filename includes the Git description. Dirty builds include a
timestamp so each release remains distinct. Salt installs it and atomically updates the `current`
symlink. Salt extracts the venv into the immutable release and uses its console
scripts for the public commands. The target must provide `/usr/bin/python3.13`;
Salt retargets the venv to that interpreter before activation.

The S6 runner ships inside this existing venv and is called by `guide`; it adds no CLI entrypoint, privileged helper, or sudo rule. Existing Salt packaging and classroom Bash/curl tools cover it, so the behavioral replacement needs no infrastructure edits. Building, deploying, and validating the updated artifact remain explicit operator work tracked in [TODO](../TODO.md).

## Runtime Directory

The daemon creates `preexec.sock` itself, so `/run/maker-guide` must be writable by the daemon UID.

For multi-user setups, the directory and socket must be accessible to the configured `allowed_group`. The daemon sets the setgid bit on the parent directory so the socket inherits its group. Pre-create `/run/maker-guide` with the correct group ownership (e.g., via systemd-tmpfiles):

```
# /etc/tmpfiles.d/maker-guide.conf
d /run/maker-guide 2750 maker-guide humans -
```

Prefer tmpfiles for this directory. If you create it from a systemd unit instead, run the setup command with root privileges, for example a `+`-prefixed `ExecStartPre`, or set `Group=humans` when `humans` is intentionally the daemon primary group.

Do not rely on an unprivileged service user to set `/run/maker-guide` ownership or group.

## Bash Hooks

Initialize Bash integration with:

```bash
eval "$(maker-guide-bash-hook init bash)"
```

The generated Bash code backgrounds `maker-guide-bash-hook before "$command"` and `maker-guide-bash-hook after "$status" "$command"` to notify the daemon before and after command execution. The command comes from `bash-preexec` history when that captures a fuller command line than `BASH_COMMAND`, for example a pipeline. Hook events are telemetry-only: they do not wait for daemon decisions and cannot prevent commands from running.
