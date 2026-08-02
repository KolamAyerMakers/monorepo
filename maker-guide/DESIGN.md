# maker-guide Progress and State Design

## Purpose

The bot helps learners throughout the Linux Foundations class. It answers questions from IRC and CLI, tracks learning progress, gives hints, validates quest work, awards score, and prepares safe context for the future LLM tutor.

The key design rule: the LLM must use learner state, but must not own learner state.

State changes must be deterministic, auditable, and repairable. The LLM may explain, hint, summarize, coach, and submit structured assessments of explicit catalog rubrics. It must not directly award score, mark quests complete, grant groups, or mutate progress.

## Requirements

The system must support:

- Per-learner progress across the 10 session Linux Foundations course.
- Course exercises with validation.
- Score, tiers, peer help votes, and side tracks.
- Public status through Unix groups where it affects identity or capability.
- Learner-visible state through files under `/makers/<handle>/`.
- IRC and CLI chat using the same chat handling path.
- LLM context that knows what each learner has already been taught.
- Instructor audit and repair after bugs or bad state transitions.
- Simple operation on one Linux server.

## Core Decision

Use SQLite as the authoritative source of truth.

SQLite session-objective and quest completions are authoritative; SSH authentication observations and Unix group membership never award or replace them.

Use `/makers/<handle>/` as a learner-readable projection.

Use Unix groups as a public capability/status projection.

Use JSONL files as an audit export, not as a recovery source for rebuilding SQLite.

Do not use `/makers` files, Unix groups, or JSONL files as the source of truth.

Run one composed course catalog for this deployment: Linux Foundations July 2026. Runtime entrypoints import the default catalog from
`maker_guide.curriculum.catalogs`, not from the concrete course data module.

If a future deployment needs multiple courses, course selection belongs in that composition module before infrastructure boundaries receive a
`CourseCatalog`.

## Why SQLite

The bot is the only writer, but that is not enough. Quest completion has one authoritative mutation and several side effects:

```text
mark quest complete
add score
maybe promote tier
record intended group grant
record projection work
record audit event
```

If this is implemented as direct file writes and the process crashes halfway, state becomes inconsistent. SQLite gives atomic transactions for authoritative state. Either the learner state mutation commits, or it does not.

External effects happen after the database commit:

```text
state.db commits first
write /makers projection from state.db
apply Unix groups from state.db
export JSONL audit records from committed audit rows
send best-effort IRC announcements if useful
```

If a projection, group change, or audit export fails, retry it from SQLite. Do not roll back committed learner progress because a side effect failed. Per-quest IRC announcements are social feedback, not repairable state; drop them when unavailable or replace them with a coalesced summary.

SQLite also makes cross-learner queries simple:

```text
who has not completed the last 3 quests?
who asked 5 help questions this week?
who is stuck on grep?
which learners are close to tier promotion?
what caused alice's current course score?
```

The file projection remains important because it is part of the class experience. Learners should be able to inspect progress with ordinary Unix commands:

```sh
cat /makers/$USER/score
cat /makers/$USER/rank
ls /makers/$USER/solves
id $USER
```

The database is the ledger. `/makers` is the dashboard.

## Storage Layout

Recommended runtime paths:

```text
/var/lib/maker-guide/state.db
/var/lib/maker-guide/audit/
/makers/<handle>/
```

`state.db` is the authoritative state.

`audit/` contains JSONL audit exports. These files are useful for human inspection, backups, and reports, but they are not used to rebuild `state.db`.

`/makers/<handle>/` is regenerated from SQLite whenever needed.

Because SQLite is the source of truth, operations must include SQLite backups. JSONL audit files are not a substitute for database backups.

## Repair Guarantees

The system must support two explicit repair commands:

```sh
maker-guide-sync-derived-data
maker-guide-sync-groups
```

The dependency direction is strict:

```text
state.db -> /makers
state.db -> Unix groups
state.db -> JSONL audit export
```

### `maker-guide-sync-derived-data`

Synchronizes `/makers/<handle>/` from `state.db`.

Expected use:

```sh
maker-guide-sync-derived-data
```

Requirements:

- Recreates every learner directory under `/makers`.
- Recreates `rank`, `score`, `tier`, `joined`, `solves/`, `adoptions/`, and `tracks/lockouts`.
- Removes stale projection files that no longer exist in SQLite.
- Takes `/makers/.sync.lock` before reading projection state and writing files, so only one sync writes a makers root at a time.
- Writes files through unique temporary paths in the destination directory and atomic rename.
- Removes stale projection files only while holding the makers-root lock.
- Sets ownership and permissions consistently.
- Never trusts existing `/makers` contents.

`/makers` is disposable. If it is wrong, stop scheduled syncs, delete it, and synchronize it from SQLite.

### `maker-guide-sync-groups`

Reconciles Unix groups from `state.db`.

Expected use:

```sh
maker-guide-sync-groups
```

Requirements:

- Reads intended group membership from SQLite.
- Compares it with actual system group membership.
- Applies missing grants and removals through narrow privileged helpers.
- Supports a dry-run mode before mutation.
- Never infers learner progress from the current Unix groups.

Unix groups are a capability/status projection. If groups drift, sync them from SQLite.

## Identity Model

The syllabus already defines one handle across Unix, IRC, and Forgejo.

The bot should treat the handle as the learner primary key.

For CLI chat:

```text
Unix username -> learner handle
```

For IRC chat:

```text
IRC nickname -> learner handle
```

This is valid because accounts are PAM-backed and share the same handle. If later aliases or renames are needed, add an identity mapping table.

## Chat Model

IRC and CLI should use one chat handling path.

Current shape should evolve toward:

```python
ChatRequest(
    text="why does grep not find my word?",
    visibility="public" | "private",
    context=CliChatContext(...) | IrcChatContext(...),
)
```

Suggested context shape:

```python
CliChatContext(
    username="alice",
    terminal="/dev/pts/2",
)
```

```python
IrcChatContext(
    nickname="alice",
    target="#help",
    reply_target="#help",
)
```

For IRC private messages:

```python
IrcChatContext(
    nickname="alice",
    target="guide",
    reply_target="alice",
)
```

Do not keep a generic `sender` if context already has `username` or `nickname`. The identity vocabulary differs by source.

The chat handler should resolve a learner handle from context before building an LLM prompt.

## Visibility

Visibility should be only:

```text
public
private
```

Use `context` to distinguish CLI vs IRC.

Examples:

```text
IRC #help message: visibility=public, context=IrcChatContext(...)
IRC private message: visibility=private, context=IrcChatContext(...)
CLI helper: visibility=private, context=CliChatContext(...)
```

Visibility answers: who can see this?

Context answers: what transport/session did this come from?

## Progress Model

Progress has four categories:

```text
learning progress
achievement progress
capability/status progress
support/help history
```

Learning progress:

- Sessions reached.
- Commands introduced.
- Quests assigned.
- Quests completed.
- Quest validation attempts.
- Known stuck topics.

Achievement progress:

- Score ledger.
- Peer help votes.
- Tiers.
- Easter eggs.
- Script adoptions.

Capability/status progress:

- Cohort membership.
- `speakers`.
- `architects`.
- `makers`.

Support/help history:

- Help requests.
- Source: CLI, IRC public, IRC private.
- Visibility.
- Topic tags.
- Commands mentioned.
- Whether an LLM answered.
- Rate-limit usage.
- Instructor review markers.

### Score, Help, and Tiers

Score is the public ranking currency. Do not expose a separate learner-facing point counter. Learners should understand that score determines the live leaderboard and the top-three prize ranking.

Target score budget:

```text
quests: 80%
help: 20%
```

Quest score is the main path. A quest completion awards its catalog score once. The first, second, and third verified completions across all learners of each quest also earn `+3`, `+2`, and `+1` score. Repeating the same completed quest must return the existing completion and must not add score again.

Help score comes from peer thank-yous, not instructor-only manual awards:

```text
each learner may send one thank per course-local day
no self-vote
thank reason required
only enrolled active learners may thank or receive thanks
each giver-recipient pair is limited to three thanks per course
same-day reciprocal thanks are blocked
each accepted thank awards the recipient 10 score
```

Store each thank and its score ledger award atomically. The peer thank id is the ledger source, so retries cannot duplicate score.

Tiers are catalog definitions and learner state together:

```text
catalog: tier id, title, minimum score
SQLite: first time a learner reached each tier
```

Current tier is derived from course score and catalog thresholds. Persist tier promotions only to support one-time announcements, audit, and projection history. Do not store mutable total score as source of truth; course score is the sum of `score_ledger` rows for that course.

Recommended first thresholds assume the baseline course path is roughly 2000 score, with help score allowing learners to exceed the quest-only path:

```text
newcomer: 0 score
apprentice: 500 score
builder: 1000 score
maker: 2000 score
```

Keep thresholds simple and memorable. Avoid too many tiers; learners should understand what the next target means without reading a table every time. Tier names should describe learner progress, not production authority or server responsibility.

## Curriculum Catalog

The syllabus is for humans. The bot needs a strongly typed curriculum catalog in Python.

Do not use TOML or YAML for the core curriculum. Use frozen dataclasses so the catalog benefits from type checking, editor support, refactor safety, and CI validation.

Recommended source layout:

```text
src/maker_guide/curriculum/
  __init__.py
  models.py
  linux_foundations_2026_07.py
```

`models.py` defines the schema. `linux_foundations_2026_07.py` instantiates the course.

The Python catalog owns curriculum definitions: courses, sessions, quests, validation rules, and tier thresholds.

SQLite owns learner state: enrollment, assignments, attempts, completions, score, generated quest instances, tier promotions, intended group grants, help history, command observations, projection status, outbox work, and audit rows.

`/makers` displays what happened. The LLM receives a derived learner snapshot built from the catalog plus SQLite state.

### Core Dataclasses

```python
from dataclasses import dataclass
from datetime import date
from typing import Literal


@dataclass(frozen=True, kw_only=True, slots=True)
class Course:
    id: str
    title: str
    timezone: str
    starts_on: date
    ends_on: date
    sessions: tuple[Session, ...]
    quests: tuple[Quest, ...]
    tiers: tuple[Tier, ...]


@dataclass(frozen=True, kw_only=True, slots=True)
class Session:
    id: str
    title: str
    date: date
    introduced_commands: tuple[str, ...]
    introduced_skills: tuple[str, ...]
    learning_objectives: tuple[str, ...]
    content: tuple[ContentReference, ...]
    enrichment_skills: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True, slots=True)
class Quest:
    id: str
    title: str
    sequence: int
    available_after_session: str
    date: date
    story: str
    learner_goal: str
    prompt: str
    autonomy_checklist: tuple[str, ...]
    hints: tuple[Hint, ...]
    failure_feedback: tuple[FailureFeedback, ...]
    docs: tuple[ContentReference, ...]
    required_commands: tuple[str, ...]
    practiced_skills: tuple[str, ...]
    score: int
    validation: QuestValidation
    data: QuestData | None = None
```

### Validation Dataclasses

Use typed validation variants instead of one loose class with optional fields.

```python
@dataclass(frozen=True, kw_only=True, slots=True)
class CommandHistoryValidation:
    required_patterns: tuple[str, ...]
    observed_commands: tuple[str, ...]
    ordered: bool = False


@dataclass(frozen=True, kw_only=True, slots=True)
class InteractiveQuestionValidation:
    question: str
    expected_keywords: tuple[str, ...]


@dataclass(frozen=True, kw_only=True, slots=True)
class FileCheckValidation:
    path: str
    required_regex: str
    forbidden_regex: str | None = None


@dataclass(frozen=True, kw_only=True, slots=True)
class UserPortFileValidation:
    path: str
    required_regex_template: str
    port_formula: str = "10000+uid"


@dataclass(frozen=True, kw_only=True, slots=True)
class PathExistsValidation:
    paths: tuple[str, ...]


@dataclass(frozen=True, kw_only=True, slots=True)
class ExecutablePathValidation:
    paths: tuple[str, ...]


@dataclass(frozen=True, kw_only=True, slots=True)
class LearnerHandleQuestionValidation:
    question: str


type QuestValidationLeaf = (
    CommandHistoryValidation
    | InteractiveQuestionValidation
    | FileCheckValidation
    | UserPortFileValidation
    | PathExistsValidation
    | ExecutablePathValidation
    | LearnerHandleQuestionValidation
)


@dataclass(frozen=True, kw_only=True, slots=True)
class AllOfValidation:
    validations: tuple[QuestValidationLeaf, ...]


type QuestValidation = QuestValidationLeaf | AllOfValidation
```

Command-history patterns normally match independently. Set `ordered=True` for lifecycle checks
that must match distinct successful observations from oldest to newest; unrelated commands may
appear between required steps.

Later validation variants can be added without weakening the model:

```python
@dataclass(frozen=True, kw_only=True, slots=True)
class HttpCheckValidation:
    url_template: str
    expected_status: int


@dataclass(frozen=True, kw_only=True, slots=True)
class SystemdUserUnitValidation:
    unit_name: str
    expected_active: bool
```

### Quest Data Generation

The catalog defines the generation strategy. Per-learner generated data lives in SQLite.

```python
@dataclass(frozen=True, kw_only=True, slots=True)
class GeneratedFileData:
    path_template: str
    generator: str
    seed_strategy: Literal["learner+quest"]


type QuestData = GeneratedFileData
```

SQLite tracks the generated instance:

```text
quest_instances(handle, course_id, quest_id, seed, generated_at, expected_answer_hash)
```

Do not put per-user generated answers in the curriculum catalog.

### Tiers

```python
@dataclass(frozen=True, kw_only=True, slots=True)
class Tier:
    id: str
    minimum_score: int
    title: str
```

Side tracks such as `architects` and `speakers` should also be cataloged if their criteria become deterministic.

### Example Session

```python
S1 = Session(
    id="S1",
    title="First contact: SSH and the lay of the land",
    date=date(2026, 7, 11),
    introduced_commands=(
        "ssh",
        "whoami",
        "hostname",
        "date",
        "uptime",
        "pwd",
        "cd",
        "ls",
        "tree",
        "find",
        "cat",
        "less",
        "head",
        "tail",
        "man",
        "tldr",
        "build-website",
        "clear",
        "exit",
    ),
    introduced_skills=(
        "ssh-login",
        "shell-basics",
        "filesystem-navigation",
        "reading-files",
        "manual-pages",
        "first-site-build",
    ),
    learning_objectives=(
        "SSH into your account",
        "Understand the shell as text in and text out",
        "Navigate the filesystem",
        "Read files",
        "Ship your first page",
    ),
)
```

### Example Quest

```python
DAY_004 = Quest(
    id="day-004",
    title="Read man ls",
    sequence=4,
    available_after_session="S1",
    prompt="Read `man ls`, find what `-S` does, then quit the manual.",
    hints=(
        "Open the manual with `man ls`.",
        "Search inside the manual for `-S`.",
        "Press `q` when you are done.",
    ),
    required_commands=("man", "ls"),
    practiced_skills=("manual-pages",),
    score=25,
    validation=InteractiveQuestionValidation(
        question="What does `ls -S` do?",
        expected_keywords=("sort", "size"),
    ),
)
```

### Catalog API

Expose deterministic helpers over the dataclass catalog:

```python
class CourseCatalog:
    def session(self, session_id: str) -> Session: ...
    def quest(self, quest_id: str) -> Quest: ...
    def commands_available_through(self, session_id: str) -> frozenset[str]: ...
    def skills_available_through(self, session_id: str) -> frozenset[str]: ...
    def quests_available_through(self, session_id: str) -> tuple[Quest, ...]: ...
    def next_quest_after(self, quest_id: str | None, released_session: str) -> Quest | None: ...
```

The LLM context builder should use this API. The LLM should never parse the syllabus Markdown.

### Catalog Validation

Static typing catches shape errors. Tests must catch semantic errors.

Catalog validation tests should enforce:

- Course ids are unique.
- Session ids are unique.
- Quest ids are unique.
- Quest sequence values are unique.
- Tier ids are unique.
- Tier score thresholds are strictly increasing.
- Every `Quest.available_after_session` exists.
- Every quest command is introduced no later than `available_after_session`.
- Every practiced skill is introduced no later than `available_after_session`.
- Every quest has a target date inside the course window, on or after its availability session, and not earlier than the previous quest by sequence.
- Quest score is positive.
- Session dates are increasing.
- No empty prompts, titles, command names, or skill names.
- Quest validator regexes compile during catalog validation.
- `CommandHistoryValidation` declares non-empty `observed_commands`; each entry must also appear in the quest `required_commands`.
- `AllOfValidation` has at least one child rule.
- Generated quest data has a non-empty generator, POSIX path template, and known seed strategy.
- Learner artifact validators require concrete `~/...` paths and reject bare `~`.
- Session content references include slides, self-study, and recap resources.
- Optional enrichment skills are discoverable but cannot satisfy required quest skill gates.

These tests are part of CI. Bad curriculum data should fail before deployment.

### Current Quest Selection

"Current quest" is not stored as one mutable field. It is selected deterministically from catalog order plus SQLite learner state.

Rule:

```text
1. Resolve the learner's current course.
2. Order released incomplete quests: current session by sequence, then earlier sessions by sequence.
3. Return the first assigned or available quest in that order, assigning it first when it was not already assigned.
4. Store a new assignment in SQLite before returning it.
```

`available_after_session` is a gate. The current session has priority; `sequence` orders quests within that session and resumes the earlier-session backlog. Future quests remain unavailable.

The `now` chat intent first displays the current released incomplete session objective without validation or progress writes. Only when that objective is complete does it call current quest selection and display its prompt, writing only a first deterministic assignment. `today` remains its compatibility alias. The `check my work` intent validates practical work, while `answer <your answer>` validates conceptual answers for the current assigned incomplete quest. The LLM may phrase the response, but it does not choose a different quest or mark it complete.

### LLM Guardrails From Catalog

For each help request, deterministic code builds:

```text
current_session
commands_available_through(current_session)
skills_available_through(current_session)
pending quests
current quest hints
```

The LLM prompt must include:

```text
Treat required_commands as proof commands, not a sandbox allowlist.
Do not introduce future-session commands as the required path.
Give hints, not full solutions.
Prefer `man <command>` and `<command> --help` when relevant.
```

The catalog is therefore part of the safety boundary around the LLM.

## Persistence Layer

Use the repository pattern for SQLite access.

Application services should depend on repositories, not on raw SQL scattered through chat handlers, validators, or projection code. Repositories own SQL statements and map database rows to typed domain objects. Services own transactions and business rules.

Recommended repository boundaries:

```text
LearnerRepository
QuestProgressRepository
ScoreLedgerRepository
TierRepository
HelpInteractionRepository
CommandObservationRepository
ProjectionRepository
AuditRepository
OutboxRepository
```

Rules:

- Use Python `sqlite3` for application database access.
- Do not use SQLAlchemy ORM, SQLAlchemy Core, SQLAlchemy sessions, SQLAlchemy models, or SQLAlchemy autogenerate.
- Pass an explicit `sqlite3.Connection` into repositories.
- Keep transaction boundaries in services, not inside individual repository methods.
- Keep schema creation out of repositories. Schema changes belong only in Alembic migrations.
- Tests should create schema by running Alembic migrations, not by maintaining a second copy of `create table` SQL.

### Migrations

Use Alembic as the migration runner, but write migrations as hand-authored raw SQL. Do not import or use SQLAlchemy in application code or migration revision files. SQLAlchemy must not become the modeling layer.

Alembic may use SQLAlchemy internally in its `env.py` connection plumbing because the Alembic CLI is built around that integration. Keep that isolated under the migration tool. Do not expose SQLAlchemy engines, sessions, metadata, tables, or expressions to application code.

Migration file pattern:

```python
from alembic import op as alembic_operations


def upgrade() -> None:
    alembic_operations.execute(
        """
        create table learners (
            handle text primary key,
            joined_at text not null,
            tagline text null,
            created_at text not null
        )
        """,
    )


def downgrade() -> None:
    alembic_operations.execute("drop table learners")
```

DRY rule: Alembic migration files are the canonical schema history. Do not use Alembic autogenerate. There is no SQLAlchemy metadata model to compare against, and generating migrations from a parallel model would violate the single-schema-source rule.

Common operations:

```sh
maker-guide-db --config /etc/maker-guide/config.toml upgrade head
maker-guide-db --config /etc/maker-guide/config.toml current
maker-guide-db history
maker-guide-db --config /etc/maker-guide/config.toml revision -m "create progress tables"
maker-guide-db --config /etc/maker-guide/config.toml upgrade --sql head
maker-guide-db --database /tmp/maker-guide-dev.db upgrade head
maker-guide-db --database /tmp/maker-guide-dev.db downgrade -1
```

Use downgrade only for local development and tests. Production rollback should restore a SQLite backup, then rerun projection and group synchronization from the restored database.

## Database Tables

Initial SQLite schema should be small.

Core tables:

```text
learners
cohort_memberships
quest_assignments
quest_instances
quest_attempts
quest_completions
score_ledger
tier_promotions
group_grants
help_interactions
command_observations
projection_versions
audit_events
outbox_items
```

Do not store catalog-owned quest or tier definitions in SQLite in the initial schema. Store catalog ids in learner-state rows. If curriculum definitions can change during an active course, add a `catalog_version` column to state rows that need historical interpretation.

### learners

```text
handle text primary key
joined_at text not null
tagline text null
created_at text not null
```

### cohort_memberships

```text
handle text not null
course_id text not null
joined_at text not null
primary key (handle, course_id)
```

### course_releases

```text
course_id text primary key
session_reached text not null
released_at text not null
```

Example course id from the Python catalog:

```text
lf2607
```

### quest_assignments

```text
id integer primary key
handle text not null
course_id text not null
quest_id text not null
assigned_at text not null
source text not null
unique (handle, course_id, quest_id)
```

Assignments are learner state. Quest definitions remain in the Python catalog.

### quest_instances

```text
handle text not null
course_id text not null
quest_id text not null
seed text not null
generated_at text not null
expected_answer_hash text null
data_json text not null
primary key (handle, course_id, quest_id)
```

Use this for generated per-learner quest data. Do not put generated answers in the catalog.

### quest_attempts

```text
id integer primary key
handle text not null
course_id text not null
quest_id text not null
attempted_at text not null
source text not null
outcome text not null
failure_reason text null
evidence_json text not null
```

### quest_completions

```text
handle text not null
course_id text not null
quest_id text not null
attempt_id integer null
completed_at text not null
source text not null
primary key (handle, course_id, quest_id)
```

If `attempt_id` is present, it must point to a passed `quest_attempts` row for the same handle, course, and quest. Enforce this in repository code and with SQLite triggers so unrelated or failed attempts cannot complete a quest.

### score_ledger

```text
id integer primary key
handle text not null
course_id text not null
amount integer not null
reason text not null
related_type text null
related_id text null
created_at text not null
```

Do not store only `score = 320`. Store the ledger. Course score is a derived sum.

Quest-completion score must be idempotent. Enforce one `quest_completed` ledger row per `(handle, course_id, quest_id)` by using `related_type = 'quest'`, `related_id = quest_id`, and a partial unique index for that reason/type pair. Retries must return the existing row instead of adding score twice.

### tier_promotions

```text
handle text not null
course_id text not null
tier_id text not null
promoted_at text not null
score_total integer not null
primary key (handle, course_id, tier_id)
```

Current tier is derived from course score and catalog thresholds. This table records first-time promotions for announcements and audit.

### group_grants

```text
handle text not null
group_name text not null
intended_state text not null
reason text not null
updated_at text not null
primary key (handle, group_name)
```

This table stores intended Unix group state. The system group database is synchronized from it.

### help_interactions

```text
id integer primary key
handle text not null
source text not null
visibility text not null
question text not null
response text null
topic_tags text not null
created_at text not null
answered_at text null
```

Use JSON text for `topic_tags` at first. Do not over-normalize too early. One row represents one known learner interaction. If the bot answers, update the same row with `response` and `answered_at`.

### command_observations

```text
id integer primary key
handle text not null
course_id text not null
command text not null
cwd text not null
phase text not null
exit_status integer null
observed_at text not null
```

This table should be pruned or summarized. Shell hooks can produce a lot of data.

Command-history validators should read only successful `phase = 'after'` rows for the learner and course, and only rows observed since the relevant assignment or attempt window. Do not validate a quest from stale commands, failed commands, pre-command hook rows, or another course's observations.

Do not keep raw shell observations forever by default. They are high-volume telemetry and can contain sensitive material such as pasted tokens, private paths, failed password attempts typed in the wrong place, or command arguments copied from other systems. Long retention also makes backups larger, makes instructor review noisier, and increases the risk that future LLM context accidentally includes irrelevant private history.

Keep durable learning facts instead:

```text
quest attempts and completions
validation evidence summaries
score ledger entries
audit rows
per-day or weekly command summaries
```

Recommended default: keep raw `command_observations` until 30 days after the cohort ends. Keep summarized evidence indefinitely.

### projection_versions

```text
name text primary key
last_written_at text not null
version integer not null
```

Use this to track projection writes such as `/makers` synchronization.

### audit_events

```text
id integer primary key
event_type text not null
handle text null
source text not null
created_at text not null
payload_json text not null
exported_at text null
```

Audit rows are committed in the same SQLite transaction as the learner state change they describe. JSONL files are exported from this table after commit.

### outbox_items

```text
id integer primary key
kind text not null
status text not null
created_at text not null
processed_at text null
payload_json text not null
```

Use outbox rows for repairable non-transactional side effects: projection writes and Unix group synchronization. Do not replay every quest-completion IRC announcement from durable outbox rows; use best-effort messages or expiring/coalesced summaries if announcements become necessary.

## JSONL Audit Log

Store audit exports as a directory of JSONL segment files, not as one unbounded file. These files are append-only audit artifacts. They are not used to rebuild SQLite.

Recommended layout:

```text
/var/lib/maker-guide/audit/2026-07-11.jsonl
/var/lib/maker-guide/audit/2026-07-12.jsonl
/var/lib/maker-guide/audit/2026-07-13.jsonl
```

Date-based rotation is the default because it is easy to inspect, easy to back up, and maps well to course days. Ordering for audit reports should use the SQLite `audit_events.id` exported in each JSON object.

Segment rules:

- Append only.
- Never rewrite an existing exported audit row.
- Rotate by Singapore local date by default.
- Keep one JSON object per line.
- Include `audit_id` in every object.
- Export only committed SQLite audit rows.
- Acquire the audit-root `.export.lock` before selecting rows so only one exporter writes a root at a time.
- If export fails, retry from rows where `exported_at` is null.
- Audit readers must de-duplicate by `audit_id` because a crash after append but before marking `exported_at` can produce duplicate exported rows. The lock prevents concurrent exporters from creating those duplicates during normal operation.

Date-based files are the operational packaging. SQLite is the state authority.

Useful audit event types:

```text
learner_created
quest_assigned
quest_attempted
quest_completed
score_awarded
tier_promoted
group_grant_intended
group_revoke_intended
group_sync_applied
help_interaction_recorded
command_observed
projection_written
```

Every audit object should include:

```text
audit_id
event_type
handle, if known
source
created_at
payload JSON
```

Why keep audit exports:

- Explain why a learner got score.
- Debug automation mistakes.
- Produce instructor reports.
- Feed future analytics.

## `/makers` Projection

The syllabus wants this layout:

```text
/makers/<handle>/rank
/makers/<handle>/score
/makers/<handle>/tier
/makers/<handle>/joined
/makers/<handle>/solves/
/makers/<handle>/adoptions/
/makers/<handle>/tracks/lockouts
```

Keep it.

But generate it from SQLite.

`tracks/` is a directory. The initial required projected file inside it is `lockouts`.

Projection write rules:

- Files are root-owned or bot-owned.
- Learners can read but not write.
- Write via temporary file plus atomic rename.
- Directories are created with stable permissions.
- Projection can be regenerated completely.

Projection command:

```sh
maker-guide-sync-derived-data
```

## Unix Groups

Groups are not progress storage. Groups are capability and public status projection.

Good groups:

```text
linux-foundations
speakers
architects
makers
```

Bad groups:

```text
day-001-complete
score-320
knows-grep
help-used-4
stuck-on-pipes
```

Rule:

```text
If it changes access, permissions, or public identity: Unix group.
If it records learning detail, score, history, or LLM context: SQLite plus projection.
```

Group changes must be written to SQLite first, then applied to the system using narrow privileged helpers. The reconciliation command is:

```sh
maker-guide-sync-groups
```

## Learner Snapshot

The LLM should receive a curated snapshot, not raw database access.

Example:

```python
LearnerSnapshot(
    handle="alice",
    cohort="lf2607",
    current_session="S3",
    taught_commands=["ssh", "ls", "cat", "grep", "wc"],
    pending_quests=["day-017"],
    completed_quests=["day-001", "day-002"],
    score=180,
    tier="apprentice",
    recent_help_topics=["grep", "pipes"],
    help_requests_today=2,
    help_limit_today=5,
)
```

The snapshot should be built by deterministic code.

The LLM prompt should include:

- Course identity and bot voice.
- Current session.
- Commands taught so far.
- Current learner progress.
- Current quest, if relevant.
- Visibility: public or private.
- Rule: hints only, no full solutions.
- Rule: do not introduce commands not taught yet.
- Rule: recommend `man <command>` and `--help` often.

## Privacy Rules

Public IRC answers should avoid exposing private learner state unless the learner explicitly asks and it is safe.

Examples:

Safe public answer:

```text
guide> Try `man grep` and look for `-i`. What happens if you search case-insensitively?
```

Unsafe public answer:

```text
guide> You failed day-014 three times and lost your place in the ranking.
```

CLI and IRC private messages can use more personal context.

## LLM Role

The LLM is a tutor, not an authority.

Allowed:

- Answer questions.
- Explain errors.
- Give hints.
- Suggest next practice.
- Summarize learner progress.
- Ask a guiding question.

Not allowed:

- Mark quests complete.
- Award score.
- Change Unix groups.
- Override validation failures.
- Reveal future-session commands as solutions.

All mutations go through deterministic services.

## Services to Build

Recommended modules:

```text
maker_guide.identity.models
maker_guide.identity.service
maker_guide.enrollment.models
maker_guide.enrollment.service
maker_guide.progress.models
maker_guide.progress.store
maker_guide.progress.catalog
maker_guide.progress.service
maker_guide.progress.projection
maker_guide.progress.context
```

If that is too much upfront, start flatter:

```text
maker_guide.identity
maker_guide.enrollment
maker_guide.progress
maker_guide.quest_catalog
maker_guide.projection
maker_guide.context
```

Avoid putting this into `chat.py`. Chat should call identity, enrollment, and progress services, not own state transitions.

Service boundary:

- `identity.service.ensure_learner` creates the stable learner identity row if needed.
- `enrollment.service.enroll` creates course membership only.
- `progress.service.release_course` releases one session to the entire cohort.
- `progress.service.current_quest`, `record_attempt`, and `complete_quest` own progress mutations.

Enrollment is not progression. Quest availability starts only after a cohort release and remains cumulative through the released session.

## Main Flows

### CLI Help

```text
guide input
build ChatRequest
resolve learner from CliChatContext.username
build LearnerSnapshot
classify chat intent from request plus context
call shared chat handler
later: call LLM with snapshot
print response
record help_interaction
```

### IRC Help

```text
IRC PRIVMSG
parse sender and target
build ChatRequest
resolve learner from IrcChatContext.nickname
build LearnerSnapshot
classify chat intent from request plus context
call shared chat handler
later: call LLM with snapshot
send response to reply_target
record help_interaction
```

### Quest Chat Intents

```text
learner says: "what should I do today?"
  resolve learner
  load current quest
  respond with prompt and allowed hints

learner says: "done" / "check my work" / "am I finished?"
  resolve learner
  load current quest
  validate deterministically using available evidence
if success:
  SQLite transaction:
    quest_completion + score_ledger + possible tier promotion
    intended group changes
    projection outbox + audit row
  after commit:
    project /makers from SQLite
    apply groups from SQLite if needed
    announce in IRC best-effort if useful
    export JSONL audit row
if failure:
  record quest_attempt and audit row in SQLite
  explain the failed check
  give deterministic hint or ask a follow-up question
```

There should not be a separate learner-facing validation command in the initial design. The user interface is chat. Validation is a backend intent, not a command learners must remember.

The LLM may help classify free text into intents such as `show_current_quest`, `validate_current_quest`, `explain_failure`, or `show_progress`. For private conceptual answers, it may call one forced tool to classify each catalog-owned rubric as demonstrated, contradicted, or not demonstrated and quote the supporting answer text. Application code validates the exact component set and literal quotes, preserves deterministic forbidden-pattern vetoes, derives the final validation result, and performs every completion or score mutation. Missing, malformed, or failed tool calls contribute no semantic evidence.

### Shell Hook Observation

```text
preexec/postexec event
record command observation selectively in SQLite
possibly update quest validation evidence
record any repairable projection or group work in outbox rows
export audit row after commit
```

Do not store every shell command forever without pruning. Keep enough for validation and recent context, then summarize or expire.

Bash hooks and introspection are evidence sources. They can prove facts like "the learner ran `man ls`" or "this file exists". They should not silently award progress for every observed command unless the quest explicitly allows auto-completion. In most cases, the learner should express intent by asking the bot to check their work.

## Progress UX

The bot must always help learners answer:

```text
Where am I?
What should I do next?
What did I just unlock?
Why did my check fail?
What commands am I allowed to use?
```

Useful chat phrases later:

```sh
guide progress
guide now
guide check my work
guide commands
guide why did my last check fail?
```

IRC equivalents:

```text
!progress
!help commands
!help grep is confusing
```

Public IRC messages require one of these command prefixes or a direct bot mention. Private IRC messages are all treated as bot input.

## Implementation Milestones

Build these in order. A milestone is complete only when its acceptance checks pass.

### M1: SQLite Migration Foundation (complete)

- [x] Add Alembic configuration that reads `MAKER_GUIDE_DB_PATH`.
- [x] Add hand-written raw-SQL migrations for the initial state tables.
- [x] Add `alembic` as a runtime dependency for the `maker-guide-db` wrapper.
- [x] Add `maker-guide-db` to read `[database].path` from config and set `MAKER_GUIDE_DB_PATH` internally.
- [x] Add test helper code that creates a temporary SQLite database by running Alembic migrations.
- [x] Document local migration commands in the project README or operations docs.

Done when:

- [x] `MAKER_GUIDE_DB_PATH=/tmp/maker-guide-test.db uv run alembic upgrade head` creates the schema.
- [x] `maker-guide-db --config /tmp/config.toml upgrade head` creates the schema without a manual environment variable.
- [x] `uv run alembic history` shows the initial migration.
- [x] Tests do not maintain a second copy of schema creation SQL.
- [x] No application code imports SQLAlchemy.

### M2: Repository Layer (complete)

- [x] Add repository functions using Python `sqlite3` only.
- [x] Pass explicit `sqlite3.Connection` objects into repository functions.
- [x] Keep transactions in service code, not inside repository functions.
- [x] Add repositories for learners, quest progress, score ledger, tiers, help interactions, command observations, audit rows, outbox rows, and projections.
- [x] Add integrity guards for quest completion attempts, idempotent quest score, and course-scoped command observations.
- [x] Add unit tests for repository reads and writes against a migrated temporary database.

Done when:

- [x] Chat, validators, and projection code do not contain raw SQL.
- [x] Repository tests cover inserts, idempotent updates, uniqueness constraints, and common query paths.
- [x] Transaction tests prove a failed service call rolls back all learner-state writes.

### M3: Typed Curriculum Catalog (complete)

- [x] Add `maker_guide.curriculum.models` with frozen dataclasses.
- [x] Add `maker_guide.curriculum.linux_foundations_2026_07`.
- [x] Add tier thresholds, sessions, and the first batch of quests.
- [x] Add `sequence` to every quest.
- [x] Add `CourseCatalog` helper methods for sessions, quests, taught commands, taught skills, and ordered quest lookup.
- [x] Add content references for session slides, self-study guides, learner recaps, and quest guides.
- [x] Add presenterm-compatible `slides.md` files for each live session.
- [x] Add S1 autonomous learner content: recap, quest guides, command cards, and concept cards.
- [x] Add S2 autonomous learner content: expanded slides and recaps, day 007-011 quest guides, command cards, and concept cards.
- [x] Add S3-S10 autonomous learner content: expanded session kits, quest guides, command cards, and concept cards.
- [x] Replace old learner-facing greeting examples with `hello makers`.
- [x] Rename quest command lists to `required_commands` and treat them as proof expectations, not sandbox allowlists.
- [x] Add optional enrichment skills for deep concepts that should not gate critical-path quests.
- [x] Add composite, executable-path, generated-data, regex, and content-link validation tests.
- [x] Add catalog validation tests.

Done when:

- [x] Duplicate ids fail tests.
- [x] Duplicate quest sequences fail tests.
- [x] Quests cannot reference future-session commands or skills.
- [x] Tier thresholds are strictly increasing.
- [x] SQLite stores catalog ids and learner state, not catalog-owned definitions.
- [x] Session content paths use padded directories such as `sessions/S01/recap.md`.
- [x] Session slides are named `slides.md`.
- [x] Curriculum content uses `lf2607.kolamayermakers.org` and `lf2607.kolamayermakers.org/~username`.
- [x] S1 content describes `new@` as the onboarding door that creates an account and disconnects, not as a shell account.
- [x] Curriculum content uses daytime session language, not evening-specific wording.
- [x] S2 quests use deterministic file/path, file-content, learner-handle, and interactive validation rules.
- [x] Full-course autonomous content tests cover every introduced command, introduced skill, and catalog quest through S10.
- [x] Validation passes with `uv run ruff check --fix && uv run ruff format && uv run basedpyright && uv run pytest` and 117 tests.

### M4: Identity, Enrollment, and Progress Services (complete)

- [x] Implement identity creation through `identity.service.ensure_learner`.
- [x] Implement course enrollment through `enrollment.service.enroll` without session placement.
- [x] Implement cohort release through `progress.service.release_course`.
- [x] Implement deterministic current quest selection.
- [x] Implement quest assignment storage before returning the current quest.
- [x] Implement quest attempts and quest completions.
- [x] Implement score ledger writes.
- [x] Implement tier promotion rows for first-time tier crossings.
- [x] Write audit rows and outbox rows in the same transaction as learner-state changes.

Done when:

- [x] There is no mutable `current_quest` column.
- [x] Enrollment does not grant access before a cohort release.
- [x] Current quest prioritizes the released session, then resumes incomplete earlier sessions by sequence.
- [x] Quest completion commits completion, score, tier promotion, audit, and outbox rows atomically.
- [x] Repeating a completed quest does not double-award score.
- [x] Completion attempts are accepted only when they match the same handle, course, quest, and passed outcome.

### M5: `/makers` Projection (complete)

- [x] Implement projection writer for `rank`, `score`, `tier`, `joined`, `solves/`, `adoptions/`, and `tracks/lockouts`.
- [x] Write projection files through temporary files plus atomic rename.
- [x] Remove stale projection files not present in SQLite-derived state.
- [x] Add `maker-guide-sync-derived-data`.
- [x] Add projection outbox processing.

Done when:

- [x] Deleting `/makers/<handle>/` and running `maker-guide-sync-derived-data` recreates it from SQLite.
- [x] Projection output never depends on existing `/makers` contents.
- [x] Projection failures can be retried from SQLite and outbox rows.

### M6: Shared Chat Context (complete)

- [x] Move CLI identity into `CliChatContext.username`.
- [x] Move IRC identity into `IrcChatContext.nickname`.
- [x] Remove generic `ChatRequest.sender`.
- [x] Resolve learner handles before intent handling.
- [x] Build `LearnerSnapshot` from catalog plus SQLite.
- [x] Record help interactions through the repository layer.
- [x] Enforce public IRC command gating.

Done when:

- [x] CLI and IRC both use the same chat handling path.
- [x] Public IRC responds only to `!help` or direct bot mention.
- [x] Private IRC treats all messages as bot input.
- [x] Help interaction rows include source, visibility, question, optional response, and timing.

### M7: Quest Chat Intents (complete)

- [x] Add deterministic intent handling for `now` (`today` remains an alias).
- [x] Add deterministic intent handling for `check my work` and `am I finished`.
- [x] Add failure explanation using the latest quest attempt.
- [x] Keep learner-facing failure feedback from exposing validator internals or solution commands.
- [x] Implement at least one validation type end to end.
- [x] Ensure failed validation records a quest attempt and audit row.
- [x] Ensure successful validation uses the progress service, not direct table writes.

Done when:

- [x] `guide now` returns the assigned current quest.
- [x] `guide check my work` validates the assigned incomplete quest.
- [x] Score and completion are awarded only through deterministic services.
- [x] The LLM is not required for quest completion.

### M8: Shell Observation Pipeline (complete)

- [x] Persist selected hook observations to `command_observations`.
- [x] Add retention cleanup for raw observations until 30 days after cohort end.
- [x] Add durable validation evidence summaries.
- [x] Ensure observation-triggered awards still use DB-first service transactions.

Done when:

- [x] Raw shell observations are not kept indefinitely.
- [x] Validation can use recent observations without scanning JSONL audit files.
- [x] Quest evidence produced by hooks survives raw observation pruning.

### M9: Audit Export And Outbox Processing (complete)

- [x] Export committed `audit_events` rows to date-based JSONL files.
- [x] Mark exported audit rows after successful export.
- [x] Make export idempotent by `audit_id`.
- [x] Add outbox processing for projection work and other repairable side effects.
- [x] Add retry behavior for failed outbox items.

Done when:

- [x] JSONL export is audit-only and cannot be used to rebuild SQLite.
- [x] A crash after DB commit but before export can be repaired by rerunning the exporter.
- [x] A crash after JSONL append but before marking `exported_at` can produce duplicates safely handled by `audit_id`.

### M10: LLM Tutor Integration (complete)

- [x] Add provider abstraction.
- [x] Add prompt builder from `LearnerSnapshot`.
- [x] Add rate limits.
- [x] Log LLM requests and responses through `help_interactions` or dedicated audit rows.
- [x] Enforce taught-command and hints-only guardrails in prompts.
- [x] Keep all progress mutations outside the LLM path.

Done when:

- [x] The LLM receives curated snapshots, not database access.
- [x] The LLM cannot mark quests complete, award score, or change groups.
- [x] Public responses avoid leaking private learner state.

### M11: Unix Groups (complete)

- [x] Add narrow privileged helpers for Unix group mutation.
- [x] Add `maker-guide-sync-groups` with dry-run support.
- [x] Reconcile actual Unix groups from SQLite `group_grants` only.

Done when:

- [x] Unix groups are never read as progress state.
- [x] Group intent is written to SQLite before system group mutation.
- [x] Group drift can be repaired by `maker-guide-sync-groups`.

### M12: Operations And Recovery (complete)

- [x] Document SQLite backup and restore.
- [x] Document restore order: restore SQLite backup, run `maker-guide-sync-derived-data`, run `maker-guide-sync-groups`, rerun audit export if needed.
- [x] Add operational checks for pending outbox rows, failed audit exports, and projection drift.
- [x] Add tests that delete `/makers` and rebuild it from SQLite.
- [x] Add tests that simulate failed side effects after DB commit.

Done when:

- [x] Recovery does not depend on JSONL replay.
- [x] Derived files and Unix groups can be reconciled from SQLite.
- [x] Operators have commands to inspect migration state, projection drift, audit export backlog, and outbox backlog.

## Decisions and Defaults

Adopt these defaults unless implementation proves they are wrong:

1. Catalog location: keep the typed curriculum catalog in this repo first. Split it into a course-content package only after there are multiple courses or non-bot consumers.
2. Shell history retention: keep raw `command_observations` until 30 days after the cohort ends. Keep summaries and durable validation evidence indefinitely.
3. IRC intent parsing: in public channels, require `!help` or a direct bot mention. In private messages, treat all messages as bot input.
4. Tier thresholds: use the first threshold set from the Score, Help, and Tiers section unless the final score budget changes materially. Keep current tier derived from course score.
5. Instructor corrections: store corrections as SQLite mutations with audit rows and source `instructor`. Do not edit old audit rows.
6. Learner renames: avoid them initially. If needed, add an identity alias table instead of changing primary keys in historical rows.
7. Catalog versioning: avoid changing quest score, validation, and ordering during a live cohort. If that becomes necessary, add `catalog_version` to assignment and completion rows first.

## Recommendation

Build SQLite source of truth first, then `/makers` projection, then Unix group projection after privileged helpers exist.

Keep the first schema small. Do not model every future gamification feature immediately. Start with learners, cohort memberships, quest assignments, quest instances, attempts, completions, score ledger, tier promotions, help interactions, audit rows, outbox rows, and projection.

Then wire chat to resolve learner identity and produce a `LearnerSnapshot`. After that add quest chat intents. Only after deterministic state and chat context are stable should the LLM be added.

This gives the bot memory, gives students inspectable Unix state, and prevents the LLM from becoming an unreliable database.
