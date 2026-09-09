# S10 Self-Study Guide: Boss Fight And Graduation

Session: S10

## Study Path

1. Create notes in the classroom and keep that SSH terminal open.
2. Connect directly to Bandit from a new laptop terminal and work through a level with your team.
3. Exit Bandit to the laptop, then switch to the classroom terminal and record what worked or the exact blocker.
4. Demo the same site/report, source repo, real backend service, and README with actual evidence.
5. Publish `~/src/pages/next.md` with one dated Linux next action.

The final project demo and next page are core work. Extra Bandit levels are optional; do not sacrifice the demo to chase a level count.

S10 has no new scored session objective. For remaining reinforcement in the classroom, `guide now` shows your current session objective first if one remains; after you complete it, it shows your current quest. Optional quests are not graduation prerequisites.

## Three Contexts

| Context | Work Here |
|---|---|
| Laptop | Open separate terminal tabs for classroom SSH and direct Bandit SSH; view public sites and Forgejo in a browser. |
| Classroom | Keep this SSH tab open to edit `~/src`, run scripts and user services, keep notes, and use `guide`. |
| Bandit | Use the separate tab connected directly from your laptop to inspect puzzle files and use temporary scratch space. |

Run `whoami`, `hostname`, and `pwd` to identify the current account, machine, and directory. `~` and `$USER` change when you connect to a different account.

From your laptop, connect to the classroom if needed. Replace `your-classroom-username` with your classroom account, not your laptop username:

```bash
ssh your-classroom-username@lf2607.kolamayermakers.org
```

Keep this classroom SSH terminal open for notes and project commands.

## Bandit Start

First, in the classroom shell:

```bash
mkdir -p ~/playground
micro ~/playground/bandit-notes.md
```

Create this note structure, save with `Ctrl-S`, and quit with `Ctrl-Q` before connecting:

```markdown
# Bandit Notes

Level:
Goal:
Command tried:
Observed result or error (no passwords):
What I learned:
Next test:
```

Leave the classroom connection open. Open a **new laptop terminal window or tab** at your laptop's local shell, then connect directly to Bandit. Do not run this command inside the classroom SSH session:

```bash
ssh bandit0@bandit.labs.overthewire.org -p 2220
```

Read the login instructions and current level goal on [OverTheWire Bandit](https://overthewire.org/wargames/bandit/). Password input is invisible at SSH prompts; that is normal. Switch to your existing classroom SSH tab to update notes, then back to the Bandit tab to continue. Your classroom files and `guide` are not available inside Bandit.

Swap driver and note-taker roles. Record commands and observations, not passwords or full puzzle answers; do not publish credentials in the site, repo, or chat.

## Unknown File Workflow

On Bandit, run `pwd` and `ls -la` and read the current goal to identify the actual input. In the example below, `/absolute/path/from-the-current-level` is a placeholder: replace it with that real file path before running the commands.

```bash
work_directory="$(mktemp -d /tmp/bandit-work.XXXXXX)"
cp -- "/absolute/path/from-the-current-level" "$work_directory/input"
cd "$work_directory"
file input
strings input | less
xxd -l 128 input
```

`mktemp -d` creates a private directory with a unique name under `/tmp`; Bandit home directories are not assumed writable. If creating or copying fails, stop and read the error. Work on the copy named `input`, leaving the puzzle's original alone. `/tmp` is scratch space, not a durable place for notes. Press `q` to leave `less`.

Choose a next command from the evidence, not by running every decoder. For a file identified as a tar archive, list it before extracting into a new subdirectory:

```bash
mkdir extract
tar -tf input
tar -xf input -C extract
```

Inspect listed paths first; do not extract unexpected absolute paths or parent-directory paths. For bzip2-compressed input, keep the copy and write decoded output separately:

```bash
bzip2 -dc input > decoded
file decoded
```

If the level instead describes Base64 data, use `base64 -d input > decoded`, then `file decoded`. Printable text alone does not prove an encoding. These are tool examples, not a level's solution; the real input determines the next step.

## Stuck Table

- `Permission denied`: check username, host, port, and password.
- Password paste shows nothing: normal SSH behavior.
- `No such file`: run `pwd` and `ls -la`.
- Output is huge: pipe to `less`, `head`, or `grep`.
- File looks binary: run `file`, then `strings`, then `xxd`.
- Archive creates many files: extract in a scratch directory.
- Home is not writable: use the `/tmp` directory made by `mktemp -d`, not `~/bandit-work`.
- Team is blocked: record the goal, last command, actual error, and next test; ask for a hint without sharing passwords.

## Return Before The Demo

In the Bandit tab, run `exit` to close the SSH connection and return to your laptop shell, not the classroom. If you opened nested Bandit connections, exit those too until you are back on the laptop.

Switch to the classroom SSH tab you kept open. If that connection has closed, reconnect from the laptop using the SSH command in [Three Contexts](#three-contexts). In the classroom tab, use `whoami` and `hostname` to confirm your account and machine, then update `~/playground/bandit-notes.md`. Only then run the project commands below; they do not belong on Bandit or in your laptop's local shell.

## Demo Script

In the classroom shell, reuse the checker and helper you already built:

```bash
bash ~/scripts/site-check.sh
PORT="$(~/bin/site.sh site_port)"
printf 'Service port: %s\n' "$PORT"
curl -I "https://lf2607.kolamayermakers.org/~$USER/"
curl -I "http://127.0.0.1:$PORT/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
systemctl --user status site.service --no-pager
```

The helper prints the S8 port, `10000 + uid`. The checker verifies the static homepage and report; it does not prove the personal backend is reachable. Inspect the real HTTP codes from all three URLs. A service marked active is not enough.

Prove that the report body reaches you through each route, using a fresh classroom scratch directory so no existing file is overwritten:

```bash
demo_directory="$(mktemp -d /tmp/site-demo.XXXXXX)"
curl -fsS "https://lf2607.kolamayermakers.org/~$USER/maker-report.html" -o "$demo_directory/static-report.html"
curl -fsS "http://127.0.0.1:$PORT/maker-report.html" -o "$demo_directory/local-report.html"
curl -fsS "https://$USER.lf2607.kolamayermakers.org/maker-report.html" -o "$demo_directory/service-report.html"
diff ~/public_html/maker-report.html "$demo_directory/static-report.html"
diff ~/public_html/maker-report.html "$demo_directory/local-report.html"
diff ~/public_html/maker-report.html "$demo_directory/service-report.html"
journalctl --user -u site.service --no-pager -n 20
```

`curl -fsS` fails on HTTP errors, hides the progress meter, and still shows errors; `-o` writes the fetched body. Stop and diagnose if a request fails. Successful requests and no `diff` output mean the bodies match the generated report. Find the actual report requests in the service journal. Do not copy expected status codes into your notes as if you observed them.

Now show the source and automation:

```bash
git -C ~/src remote -v
git -C ~/src log --oneline -5
git -C ~/src status
cat ~/src/README.md
ls -l ~/src/scripts ~/src/services
systemctl --user list-timers
journalctl --user -u site-build.service --no-pager -n 20
```

On your laptop, open both public URLs and their report page, then the Forgejo repository. Replace `$USER` with your actual classroom username when typing a browser URL; browser address bars do not expand shell variables. Show the newest commit, README, and all six [handoff copies](../../quests/prepare-source-handoff.md#copy-working-files). Explain a real failure you recovered from.

`maker-report.sh` collects facts into Markdown; `build-website` and the timer render existing source into HTML. The timer does not refresh those facts or catch up missed calendar runs after downtime.

If a static URL is `404`, inspect the source and generated filename. If the personal URL is `502`, compare the local request, port, service status, and logs. If DNS fails but the local backend works, use the [platform reference](../../guides/platform-reference.md) and bring actual outputs to the instructor; a failed public request is not end-to-end success.

## Next Path Template

Edit `~/src/pages/next.md`. Adapt this real Markdown template to one action you intend to take:

```markdown
# My Next Linux Project

Path: Maintain my Linux site and service.

Next action: On 2026-10-31, rebuild my site, run my checker, and inspect service logs.

Risk: A source change could break a page.

Recovery plan: Review the last working commit and rebuild that version.

Documentation: [systemd service units](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html).

Proof: Both public URLs respond and the updated page is visible.
```

Keep a Markdown heading containing Linux and an explicit `Next action:` line with a concrete action and date. Choose your own path and documentation rather than leaving an unfilled list of possibilities.

Follow [Write the next path](../../quests/write-next-path.md) to link `next.html` from the homepage, rebuild, inspect and stage only those page changes, commit, push, and verify the page and Forgejo commit from your laptop.

## Missed-Session Accommodation

The normal graduation core includes the site, source repo, working service, and README. If you missed S8 or S9, agree with the instructor on a reduced demo that explicitly names the missing artifacts and a dated recovery action. Show what actually works and use the relevant self-study guide to finish.

## Proof Checklist

- Classroom Bandit notes record the command that mattered, its actual result, and either a solve or an honest blocker and next test, without passwords.
- The existing checker runs, both public sites open from your laptop, and fetched report bodies match the generated file via the static, local backend, and public service routes.
- Your service status and request logs agree with what you demonstrated.
- Forgejo contains the README, site/report source, and three scripts plus three units from the handoff.
- `~/src/pages/next.md` has a Linux heading, an explicit dated `Next action:`, and a documentation link; it is built, linked, committed, and pushed.

Carry out that next action after graduation. Further Bandit levels and other projects are optional ways to keep practicing.

## Docs Pointers

- [OverTheWire Bandit](https://overthewire.org/wargames/bandit/)
- [Debian Handbook](https://www.debian.org/doc/manuals/debian-handbook/)
- [Ubuntu Server documentation](https://documentation.ubuntu.com/server/)
- [Arch Wiki](https://wiki.archlinux.org/) as reference material, not a beginner install prescription.
- Read [file compression](../../concepts/file-compression.md) before extracting archives.
- Read [file encoding](../../concepts/file-encoding.md) and [number bases](../../concepts/number-bases.md) before using `xxd` heavily or assuming a file is plain text.
