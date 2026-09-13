# Linux Foundations S10

Session: S10

Boss fight, demos, graduation

<!-- end_slide -->

# The Real Point

The point was never the checklist.

The point was becoming the kind of person who can keep going. Show the same site, report, checker, helper, service, and source handoff you have built throughout the course.

<!-- end_slide -->

# Know Which Machine

- Laptop: separate terminal tabs for classroom SSH and direct Bandit SSH, plus the outside browser.
- Classroom: keep this SSH tab open for your site, `~/src`, scripts, user services, notes, and `guide`.
- Bandit: connect directly from a new laptop terminal tab for puzzle accounts and files, not your classroom project.

Use `whoami`, `hostname`, and `pwd` when unsure. `$USER` and `~` refer to the current machine's account, not always your classroom account.

<!-- end_slide -->

# Notes Before Connecting

In your existing classroom SSH terminal, create the note file before starting Bandit:

```bash
mkdir -p ~/playground
micro ~/playground/bandit-notes.md
```

Record the level, goal, command tried, actual result, and next test. Save with `Ctrl-S` and quit with `Ctrl-Q`. Never put passwords in notes you will publish or share.

Keep the classroom connection open. In a **new laptop terminal window or tab**, run this from your laptop's local shell, not from the classroom:

```bash
ssh bandit0@bandit.labs.overthewire.org -p 2220
```

Read the login instructions and each goal on [OverTheWire Bandit](https://overthewire.org/wargames/bandit/).

<!-- end_slide -->

# Boss Fight

Teams work through a level: one person drives, another reads the goal and records the method, then swap.

Hands-on now: work in teams, keep notes, and ask publicly when blocked.

Use the tools. Read the errors. Ask publicly about the command and error, not the password or answer.

Switch to the classroom SSH tab to update notes, then back to the Bandit tab to continue. `guide` runs in the classroom, not on Bandit.

Inspect with `ls -la` and `file`, then choose a tool for the actual file. For writable scratch space on Bandit, use `mktemp -d /tmp/bandit-work.XXXXXX`; do not assume its home directory is writable. Follow the [file workflow](self-study.md#unknown-file-workflow), not a list of guessed decoders.

<!-- end_slide -->

# Return To The Classroom

In the Bandit tab, run `exit` to return to your laptop shell. Exit any nested Bandit connections too. This does not take you into the classroom.

Switch to the classroom SSH tab you kept open. Only if it disconnected, reconnect from your laptop using your classroom username, not your laptop's `$USER`:

```bash
ssh your-classroom-username@lf2607.kolamayermakers.org
```

Replace `your-classroom-username` before running it. In the classroom tab, confirm your account and machine with `whoami` and `hostname`, then update `~/playground/bandit-notes.md` before the site demo.

<!-- end_slide -->

# Site Tour

Required demo: site, source repo, running service, README, and one recovery story.

In the classroom shell, reuse your checker and helper:

```bash
bash ~/scripts/site-check.sh "" maker-report.html
PORT="$(~/bin/site.sh site_port)"
curl -I "https://lf2607.kolamayermakers.org/~$USER/"
curl -I "http://127.0.0.1:$PORT/"
curl -I "https://$USER.lf2607.kolamayermakers.org/"
systemctl --user status site.service --no-pager
journalctl --user -u site.service --no-pager -n 20
```

Read the real outputs. Service status alone does not prove a working backend.

<!-- end_slide -->

# Prove The Whole Path

Follow the [demo script](self-study.md#demo-script): fetch the report from the static URL, localhost service port, and public service URL, then compare each body with `~/public_html/maker-report.html`.

In your laptop browser, open both public URLs and the report page. Show the Forgejo README, newest commit, three scripts, and three units. Explain which command collects report facts and which only rebuilds HTML.

Use actual results and one real recovery story. If a request fails, show the error and diagnose it instead of claiming success.

<!-- end_slide -->

# Publish Your Next Step

Create `~/src/pages/next.md` using the [next-path template](self-study.md#next-path-template). Keep a real Markdown heading containing Linux and an explicit `Next action:` line with an action and date.

Link `next.html` from the homepage, rebuild, then inspect and stage only the intended page changes, commit, and push. Verify the page and commit from your laptop.

<!-- end_slide -->

# Exit Goal

Graduate with a live site and report, a reachable source repo containing the working scripts and units, a service that actually answers requests, a useful README, and a published Linux next step.

Missed-session accommodation: agree with the instructor on what is missing and when to recover it. A reduced demo must say so explicitly.
<!-- end_slide -->

# Keep Going

Carry out the dated `Next action:` on your page. Keep the repo and working copies in sync after future edits, and verify pushes in Forgejo.

Optional: more Bandit levels, a homelab, or teaching a command to someone else. No next class is required to take the first step.

<!-- end_slide -->

# Final Proof

The proof is not that you remember every command.

The proof is that you can read, test, recover, and explain.

S10 has no new scored session objective. Use the guide for remaining reinforcement in the classroom: `guide now` shows your current session objective first if one remains; after you complete it, it shows your current quest.

Use `guide answer 'your answer'` for prompted answers and `guide check` after practice. Optional quest completion is not a graduation prerequisite.
