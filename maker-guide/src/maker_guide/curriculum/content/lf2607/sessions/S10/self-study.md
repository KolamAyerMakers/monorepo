# S10 Self-Study: Show What You Can Do

Session: S10

2026-10-24

## Three-Hour Shape

| Minutes | Activity |
|---|---|
| 0-10 | Choose an investigation and demo focus |
| 10-30 | Investigate one unfamiliar question |
| 30-45 | Share the method and observations |
| 45-55 | Break |
| 55-75 | Prepare and rehearse |
| 75-150 | Twelve five-minute demos plus 15 minutes for transitions |
| 150-170 | Choose a next action and date |
| 170-180 | Closing reflection |

Protect the 75-minute demo block. Stop the investigation after 20 minutes even if it remains unresolved. Explain your method rather than racing to finish the most puzzles.

The main work is a five-minute demonstration with self-chosen evidence and a real recovery explanation. The detailed commands below are fallback tools for preparation or recovery, not a script everyone must perform.

## Bounded Unfamiliar Investigation

Choose one question small enough to investigate in 20 minutes. You can inspect a file provided by the instructor, explain an unfamiliar command option or service log line, or try an optional [Bandit puzzle](https://overthewire.org/wargames/bandit/). No solve count is required.

Work alone or in pairs. If pairing, swap the reader and keyboard roles halfway through. Record the question, documentation or command used, actual observation, and next test. A well-evidenced blocker is a useful result.

Do not execute unknown files, try commands against other learners' services, or make privileged changes. Use read-only inspection first. For a file task, the instructor must identify the exact input and permitted scope; do not scan unrelated private files.

## Three Contexts

| Context | Work Here |
|---|---|
| Laptop | Browser, classroom SSH tab, and a separate direct Bandit SSH tab if chosen |
| Classroom | Your site, source, scripts, user services, and durable notes |
| Bandit | Only the optional puzzle's accounts and files |

When unsure, run:

```bash
whoami
hostname
pwd
```

`~` and `$USER` refer to the current machine's account. From your laptop, reconnect to the classroom only if needed, replacing the username before running:

```bash
ssh your-classroom-username@lf2607.kolamayermakers.org
```

Keep that classroom terminal open. You can keep private investigation notes there:

```bash
mkdir -p ~/playground
micro ~/playground/investigation-notes.md
```

Save with `Ctrl-S`, quit with `Ctrl-Q`, and omit all passwords, tokens, and private puzzle answers from shared notes.

## Optional Bandit Start

Read the current login instructions and goal on [OverTheWire Bandit](https://overthewire.org/wargames/bandit/). From a **new laptop terminal at the local shell**, not inside classroom SSH:

```bash
ssh bandit0@bandit.labs.overthewire.org -p 2220
```

SSH password input is invisible. Do not put passwords in command lines, public notes, the site, repository, or chat. Keep your classroom notes in the classroom tab; they are not files on Bandit.

For an unfamiliar puzzle file, inspect the goal and actual paths before choosing a tool:

```bash
pwd
ls -la
```

Use `file` with the actual filename and read its result. If you need writable scratch space, do not assume Bandit's home is writable. Replace the placeholder path below with the real puzzle input before running, one command at a time:

```bash
work_directory="$(mktemp -d /tmp/bandit-work.XXXXXX)"
cp -- /absolute/path/from-the-current-level "$work_directory/input"
file "$work_directory/input"
xxd -l 128 "$work_directory/input"
```

Stop if directory creation or copying fails. Keep the original untouched. Do not execute the copy. Choose any decoding from actual evidence, not a list of guessed decoders. Consult [file encoding](../../concepts/file-encoding.md) or [file compression](../../concepts/file-compression.md) if relevant; these are optional references, not a requirement to decode an archive today.

At the time limit, note the result and next safe test. Run `exit` in the Bandit tab to return to your laptop; exit nested connections too. Then switch to the classroom SSH tab, confirm account and hostname, and update your notes. Exiting Bandit does not put you in the classroom automatically.

## Plan Your Five Minutes

Choose one claim from your work: a useful script, an automatic refresh, a reachable page, a repaired service, or a handoff another person could operate. Decide what evidence would convince someone of that claim.

| Time | Content |
|---|---|
| 0:00-0:30 | Name what you chose and its purpose |
| 0:30-3:00 | Demonstrate the result with your chosen evidence |
| 3:00-4:30 | Explain one real failure and recovery |
| 4:30-5:00 | State what you learned and take one question |

Use evidence you actually observed. Logs, page bodies, source changes, and peer feedback can all be useful; no fixed tour of every course artifact is required. Recorded evidence is acceptable if access is unavailable, provided you state when it was collected and what cannot be verified live.

For recovery, explain the symptom, observation that narrowed the cause, repair, and confirming result. Do not stage a risky break during the demo. If you lack a recovered example, agree with the instructor on a safe preparation exercise, such as the [owner-operated README test](../../quests/write-readme.md#peer-operation-test), before the demo block. If still unresolved, show the blocker honestly and agree on a dated recovery action rather than fabricating a story.

## Demo Script

This is fallback evidence for a site/service claim, not a required presentation sequence. Run it in the classroom, using only the parts that support your chosen claim. For automatic-refresh evidence instead, use [Witness Automatic Publication](../S09/self-study.md#witness-automatic-publication); do not call a manually started build automatic.

For stable body comparisons, pause automation and inspect the build state first:

```bash
systemctl --user stop site-build.timer
systemctl --user status site-build.service --no-pager
```

If the build is still `activating`, wait until it finishes and inspect again. Do not interrupt publication. Let any standalone build finish too, and do not launch another during the comparisons. If you have not created these units, name that missing work; do not create empty files for a demonstration.

Compute the classroom port directly; no helper is needed:

```bash
service_port="$((10000 + $(id -u)))"
printf 'Service port: %s\n' "$service_port"
systemctl --user cat site.service
bash ~/scripts/site-check.sh "" maker-report.html
systemctl --user status site.service --no-pager
```

If the port exceeds `65535` or does not match the unit, stop and ask the instructor rather than choosing another port. The unit needs `WorkingDirectory=%h` and `ExecStart=/usr/bin/caddy file-server --listen :12345 --root %h/public_html --access-log`, with your numeric port in place of `12345`; see the [complete S8 unit](../S08/self-study.md#2-create-the-user-unit). The publisher swaps its output directory, so the explicit root must follow the current published path rather than an old working directory.

Shared Caddy handles public HTTPS and forwards requests to personal Caddy over loopback HTTP. Same software, two separate processes; no `--domain` or shared configuration changes. `file-server` disables its admin API. Control personal Caddy with `systemctl --user`, never `caddy stop` or `caddy reload`, which can target shared Caddy's admin endpoint. The root is not a sandbox: keep secrets and symlinks to private files out of the published tree.

The checker covers the static homepage and report, not the personal service hostname. A successful static check or active service is not proof of the whole backend route.

## Compare Report Bodies

With publishing paused, make a fresh scratch directory and snapshot the generated report:

```bash
demo_directory="$(mktemp -d /tmp/site-demo.XXXXXX)"
cp ~/public_html/maker-report.html "$demo_directory/generated-report.html"
curl --max-time 10 -fsS "https://lf2607.kolamayermakers.org/~$USER/maker-report.html" -o "$demo_directory/static-report.html"
curl --max-time 10 -fsS "http://127.0.0.1:$service_port/maker-report.html" -o "$demo_directory/local-report.html"
curl --max-time 10 -fsS "https://$USER.lf2607.kolamayermakers.org/maker-report.html" -o "$demo_directory/service-report.html"
diff -u "$demo_directory/generated-report.html" "$demo_directory/static-report.html"
diff -u "$demo_directory/generated-report.html" "$demo_directory/local-report.html"
diff -u "$demo_directory/generated-report.html" "$demo_directory/service-report.html"
journalctl --user -u site.service --no-pager -n 20
```

Run one command at a time. Stop if creating, copying, or fetching fails; do not compare a missing or partial response as though it succeeded. `curl -f` fails on HTTP errors, `-sS` hides progress but retains errors, and `--max-time 10` bounds each request. No `diff` output with exit `0` means matching bodies; exit `1` means differences and higher values mean comparison errors.

Point to actual report requests in the web-service journal: `--access-log` records structured fields `request.method`, `request.uri`, `status`, and a timestamp or time (`ts` in JSON). Journal formatting can differ from the foreground terminal. From your laptop browser, open the [static report](https://lf2607.kolamayermakers.org/~your-handle/maker-report.html) and [service report](https://your-handle.lf2607.kolamayermakers.org/maker-report.html), replacing `your-handle` with your classroom username. Inspect the content, not just headers. Requests from the classroom machine can use local host mappings and are not a substitute for the outside view.

When finished comparing or reviewing source, restart the existing reviewed hourly timer:

```bash
systemctl --user start site-build.timer
systemctl --user list-timers --all site-build.timer
```

Do not leave a classroom-speed timer running; use the [hourly schedule](../S09/self-study.md#hourly-schedule). If a failure means it is unsafe to restart automation, leave it stopped, document why, and ask the instructor for help.

## Source And Automation Evidence

For a handoff claim, inspect the existing README and source copies:

```bash
git -C ~/src remote -v
git -C ~/src log --oneline -5
git -C ~/src status
cat ~/src/README.md
ls -l ~/src/scripts ~/src/services
journalctl --user -u site-build.service --no-pager -n 50
```

Open Forgejo from your laptop and verify the actual README, site source, and [five handoff copies](../../quests/prepare-source-handoff.md#copy-working-files): two scripts and three units. A local log alone does not prove they were pushed. Show how a peer used the README and what you clarified.

For an automation claim, explain that the oneshot's pre-start regenerates report Markdown before npm builds. npm alone does not collect fresh facts. A failed report must prevent building and preserve the last valid result; [report preparation](../S09/self-study.md#report-safety-gate) explains safe replacement of older scripts. A schedule listing is not evidence of changed published facts.

## Recovery Pointers

| Observation | Narrow The Cause |
|---|---|
| Static report `404` | Inspect `~/src/pages/maker-report.md`, the build log, and `~/public_html/maker-report.html`. |
| Personal URL `502` | Compare the local request, assigned numeric port, unit state, and web-service journal. |
| Local response fresh, browser stale | Inspect actual bodies, browser refresh, and personal Caddy's explicit `--root`. |
| Pre-start failure | Read the report error; do not bypass it to build partial facts. |
| Local works, public hostname fails | Collect hostname and request evidence for the instructor; do not change DNS, shared Caddy settings, or TLS verification. |

Use the [S9 self-study](../S09/self-study.md), [S8 unit recovery](../S08/self-study.md#8-restore-and-recover), and [source restoration procedure](../../quests/prepare-source-handoff.md#restore-from-source) for repairs. Keep the serving unit aligned with the S8 Caddy example. Owners operate their own accounts even when peers help read instructions. Do not exchange passwords or stop other people's processes.

## Next Path Template

Choose one action and a date. Keep it in a calendar, private note, README, or a public page if that audience is useful. Any clear wording is acceptable; no required Linux heading or exact label.

For example:

```markdown
# Keep My Site Useful

On 2026-10-31, I will follow my README to refresh the report and inspect the public result.

I will record the changed report date and one instruction that needs improving.

Reference: [systemd service units](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html).
```

Adapt the action and date to something you intend to do. A documentation link can help but is not a formatting gate. Follow [Write the next path](../../quests/write-next-path.md) if you choose to publish; it includes safe pause/build/Git instructions. Do not publish private plans merely to satisfy a page requirement.

## Unfinished Work

Agree with the instructor on the scope of your demo if earlier work is incomplete. Name what works, what is missing, and the next recovery action with a date. The audience should be able to distinguish observed success from planned work.

After the course, carry out the chosen action and record what happened. Further puzzles, a homelab, or teaching someone a command are options, not new requirements.
