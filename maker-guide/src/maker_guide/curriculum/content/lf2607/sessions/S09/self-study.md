# S9 Self-Study Guide: Timers, Text, Polish

Session: S9

## Study Path

Live core:

1. Create and enable a user systemd timer for site rebuilds.
2. Use `sed` for one substitution.
3. Use `awk` for one field extraction.
4. Create a vim note: insert, escape, save, quit.
5. Write a README that explains the site, build, service, and recovery path.
6. Enable the webring through source configuration, then rebuild twice.
7. Prepare the source handoff: copy working scripts and units into the existing repo, commit, and push.

In the classroom, start with `guide now` for your current session objective. Follow these seven steps in order, using the checkpoint routine after each step.

Cron and extra Bandit warmup are optional. S10 is on **2026-10-24**.

## Checkpoint Routine

After completing a step, run `guide now`:

- It checks one task and shows the next on success.
- Otherwise, follow the feedback, fix the problem, and try again.

Run `guide now` before starting a quest. Use `guide answer 'your answer'` when asked; `guide check` is an optional explicit check.

## Keep The Same Project

```bash
bash ~/scripts/site-check.sh "" maker-report.html
~/bin/site.sh site_port
systemctl --user status site.service
git -C ~/src status
```

Keep `~/scripts/maker-report.sh`, `~/scripts/site-check.sh`, `~/bin/site.sh`, and `~/.config/systemd/user/site.service` working. Do not replace the site or start a new repository. If you missed earlier work, use the S5-S8 guides to recover it; use the [S4 Git workflow](../S04/self-study.md#git-workflow) if `~/src` is not yet a repository.

## Timer Files

Create the directory and edit the two files. Inspect existing contents rather than replacing a working unit blindly.

```bash
mkdir -p ~/.config/systemd/user
micro ~/.config/systemd/user/site-build.service
micro ~/.config/systemd/user/site-build.timer
```

`~/.config/systemd/user/site-build.service`:

```ini
[Unit]
Description=Build my site

[Service]
Type=oneshot
WorkingDirectory=%h/src
ExecStart=/usr/local/bin/npm run build
```

`~/.config/systemd/user/site-build.timer`:

```ini
[Unit]
Description=Build my site every hour

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h

[Install]
WantedBy=timers.target
```

`%h` means your home directory. In this site's starter, `/usr/local/bin/npm run build` in `~/src` runs the prebuild asset sync and writes the same output as `build-website`.

The timer activates the matching `site-build.service`, not the long-running `site.service`. `OnBootSec=5min` is relative to boot; if already past, it can fire immediately when enabled. `OnUnitActiveSec=1h` schedules another run relative to the service's last activation. This is a monotonic timer, not a calendar schedule: it does not replay missed calendar runs after downtime.

Rebuilding renders the existing `~/src/pages/maker-report.md`; it does not rerun `maker-report.sh` or refresh its collected facts. To refresh those deliberately, run `~/scripts/maker-report.sh "My Maker Report"` first, then rebuild.

Activate and prove it:

```bash
systemctl --user daemon-reload
systemctl --user enable --now site-build.timer
systemctl --user start site-build.service
systemctl --user list-timers
journalctl --user -u site-build.service --no-pager -n 50
bash ~/scripts/site-check.sh "" maker-report.html
```

Find the next run and a completed build in the actual output. A successful `Type=oneshot` service normally becomes inactive after finishing. If automation stops at logout, inspect `loginctl show-user "$USER" -p Linger` and ask the instructor; do not change system settings yourself.

Checkpoint before sed, using the [checkpoint routine](#checkpoint-routine):

```bash
guide now
```

## Text Transform Anatomy

```bash
printf '# heading\n' | sed 's/^# \(.*\)$/<h1>\1<\/h1>/'
```

Expected output: `<h1>heading</h1>`.

- `s/pattern/replacement/` substitutes matching text.
- `^` and `$` anchor the start and end of the line; `# ` matches a literal hash and space.
- `.` means any character; `*` repeats it zero or more times. This is regex syntax, not a filename glob.
- `\(.*\)` captures the heading text; `\1` inserts it into the replacement.
- `\/` keeps the closing HTML slash from ending the substitution. Single quotes protect the expression from the shell.

Predict which line changes, then try it:

```bash
printf '%s\n' '# My report' 'ordinary line' | sed 's/^# \(.*\)$/<h1>\1<\/h1>/'
```

The output is `<h1>My report</h1>` followed by unchanged `ordinary line`. Keep using the site builder for real Markdown; this tiny exercise does not handle general Markdown or HTML escaping.

Checkpoint before awk, using the [checkpoint routine](#checkpoint-routine):

```bash
guide now
```

## Awk Fields

```bash
awk -F: '{print $1}' /etc/passwd
```

`-F:` splits each record at `:`; `{print $1}` prints the first field. Single quotes protect awk's `$1` from the shell. These are local account names, not a complete classroom roster. Change `$1` to `$7` and compare those shell paths with the report's `cut -d: -f7` pipeline.

Checkpoint before vim, using the [checkpoint routine](#checkpoint-routine):

```bash
guide now
```

## Vim New File

```bash
mkdir -p ~/playground
vim ~/playground/vim-note.txt
```

1. If this is a new file, press `i` to enter insert mode. If it already has notes, keep them and add a sentence.
2. Type `My timer rebuilds existing site source.`
3. Press Esc to leave insert mode.
4. Type `:wq` and press Enter to write the file and quit.
5. At the shell, run `cat ~/playground/vim-note.txt` to see the saved text.

`:w` saves without quitting. Esc, `:q!`, Enter quits without saving your changes. You may keep using Micro for other edits; creating this one vim note is core practice.

Checkpoint before the README, using the [checkpoint routine](#checkpoint-routine):

```bash
guide now
```

## README Minimum

Open `micro ~/src/README.md` and preserve useful existing content. Add a Markdown title and explain:

- What the site and report show, with links to both public URLs. In the classroom shell the URL forms are `"https://lf2607.kolamayermakers.org/~$USER/"` and `"https://$USER.lf2607.kolamayermakers.org/"`; use your actual username in Markdown links.
- How to generate fresh facts with `~/scripts/maker-report.sh "My Maker Report"`, render them with `build-website`, and verify with `bash ~/scripts/site-check.sh "" maker-report.html`.
- How to inspect the service with `systemctl --user status site.service` and `journalctl --user -u site.service --no-pager -n 20`.
- How to inspect `site-build.timer`, and why rebuilding alone does not collect new report facts or catch up missed calendar runs.
- What `pages/`, `scripts/`, and `services/` contain, and where the working scripts and units must be restored.
- One real failure and recovery, plus required tools and the classroom-specific port and hostnames that need adapting elsewhere.

Save the README and quit Micro with `Ctrl-S`, then `Ctrl-Q`. The file copies and scoped Git workflow come after the webring step.

Checkpoint before the webring, using the [checkpoint routine](#checkpoint-routine):

```bash
guide now
```

## Webring Source Setting

Enable the webring in source configuration, not generated HTML:

```bash
micro ~/src/site.toml
build-website
grep -i webring ~/public_html/index.html
```

The setting must be `webring = true`. Run `build-website` a second time and repeat the `grep`. Open the static homepage in your laptop browser after both builds and confirm there is one clean set of previous/next links.

Checkpoint before the source handoff, using the [checkpoint routine](#checkpoint-routine):

```bash
guide now
```

## Prepare Source Handoff

Follow [Prepare a source handoff](../../quests/prepare-source-handoff.md) now for the exact copy paths and scoped Git commands. Copy the report script, checker, and helper into `~/src/scripts/`, and the three units into `~/src/services/`. Keep active originals in place and inspect before overwriting an existing copy.

Complete the inspect, stage, commit, push workflow for the README, report page, source setting, scripts, and units. Verify the files in Forgejo; a Git log listing alone is not a portable backup.

Final S9 checkpoint, using the [checkpoint routine](#checkpoint-routine):

```bash
guide now
```

Once all seven core steps are recorded as complete, `guide now` shows your current quest. Remaining quests are optional reinforcement, not graduation prerequisites.

## Optional Cron Practice

Follow [Try cron and remove it](../../quests/try-cron-and-remove-it.md). It explains choosing Micro, saving the existing crontab, waiting for date output, and removing only your demo line. Keep all unrelated jobs; never use `crontab -r` for this exercise.

## Optional Bandit Warmup

Practice on known classroom files first:

```bash
ls -la ~/src/pages
cat ~/src/README.md
grep '^#' ~/src/pages/*.md | sort | uniq
```

Say what each stage prints. S10 uses the same method: read the level goal, inspect files, try one command, and note what worked, without memorizing answers.

## Troubleshooting

- Cron did nothing: use absolute paths and inspect `~/cron.log`.
- Timer did nothing: run `systemctl --user list-timers`, start `site-build.service` manually, and read its journal.
- Sed output is unchanged: test the regular expression against one known input line.
- Vim feels stuck: press Esc, type `:q!`, and press Enter.

## Proof Checklist

- You ran `guide now` after each step and followed its feedback before continuing.
- Both timer unit files exist, `site-build.timer` is enabled and listed, and its paired service completed a build.
- You ran the sed and awk transforms and can explain their output.
- `~/playground/vim-note.txt` contains the sentence you saved from vim.
- `~/src/README.md`, the six handoff copies in `scripts/` and `services/`, and `site.toml` are committed and visible in Forgejo.
- The original report/checker scripts, helper, and active units remain in their working paths.
- Generated HTML contains webring navigation after two rebuilds, without duplicate output.
- If you tried optional cron, `~/cron.log` has date lines and only your demo job was removed.

## Docs Pointers

- Run `man 5 crontab`, `man sed`, `man awk`, and `man vim`.
- Read [systemd timer units](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html).
- For webring work, follow [enable-webring](../../quests/enable-webring.md) and use the exact `webring = true` setting.
- Read [Regular Expression](../../concepts/regular-expression.md) before changing sed patterns.
- Read the [GNU sed manual](https://www.gnu.org/software/sed/manual/sed.html) and [GNU awk manual](https://www.gnu.org/software/gawk/manual/gawk.html) when the one-liners stop being enough.
- Read [One-Liners](../../concepts/oneliner.md) before compressing timer checks, text transforms, and publishing commands into one prompt line.
