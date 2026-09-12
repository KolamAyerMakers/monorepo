# Linux Foundations S9

Session: S9

Polish the same project: timers, text, README, webring

<!-- end_slide -->

# Today's Story

Useful systems run again tomorrow without you remembering.

Keep your static site, report, checker, `~/bin/site.sh`, and `site.service`. Today you automate rebuilding and make that work portable.

<!-- end_slide -->

# Hands-On Spine

Required live work:

1. Create and enable a user build timer, then read a successful build log.
2. Transform a heading with `sed`.
3. Extract fields with `awk`.
4. Save a new note with vim.
5. Write the README.
6. Enable the webring from source and rebuild twice.
7. Prepare the source handoff: copy working scripts and units into the existing repo, commit, and push.

Start with `guide now` for your current session objective. Use the checkpoint routine after each of these seven steps.

Use the [self-study guide](self-study.md) for the complete commands. Cron is optional, not a prerequisite.

<!-- end_slide -->

# Checkpoint Routine

After completing a step, start with:

```bash
guide now
```

- It checks one task and shows the next on success.
- Otherwise, follow the feedback and try again.

Run `guide now` before starting a quest. Use `guide answer` when asked; `guide check` is an optional explicit check.

<!-- end_slide -->

# Create The Timer Pair

Hands-on now: create these files with Micro. Inspect any existing contents before changing them.

```bash
mkdir -p ~/.config/systemd/user
micro ~/.config/systemd/user/site-build.service
micro ~/.config/systemd/user/site-build.timer
```

Use the complete [timer files](self-study.md#timer-files): the service runs `/usr/local/bin/npm run build` in `%h/src`; the timer uses `OnBootSec=5min` and `OnUnitActiveSec=1h`.

This rebuild renders existing report Markdown. It does not rerun `maker-report.sh` or refresh collected facts. The monotonic schedule does not catch up missed calendar runs after downtime.

<!-- end_slide -->

# Activate And Prove It

```bash
systemctl --user daemon-reload
systemctl --user enable --now site-build.timer
systemctl --user start site-build.service
systemctl --user list-timers
journalctl --user -u site-build.service --no-pager -n 50
bash ~/scripts/site-check.sh "" maker-report.html
```

Find the next timer run and the completed build in the real output. An inactive oneshot service after success is normal; a failed build is not.

Checkpoint: use the checkpoint routine with `guide now` before sed.

<!-- end_slide -->

# One Small Regex

```bash
printf '# heading\n' | sed 's/^# \(.*\)$/<h1>\1<\/h1>/'
```

Expected: `<h1>heading</h1>`. `s/from/to/` substitutes a match. `^` and `$` anchor the line; `# ` is literal; `.*` matches the remaining text. `\( ... \)` captures it and `\1` puts it in the replacement. `\/` is a literal slash inside the `/`-delimited substitution.

Try both a heading and an ordinary line:

```bash
printf '%s\n' '# My report' 'ordinary line' | sed 's/^# \(.*\)$/<h1>\1<\/h1>/'
```

Only the heading changes. This is a regex exercise, not a replacement for the site's Markdown builder.

Checkpoint: use the checkpoint routine with `guide now` before awk.

<!-- end_slide -->

# Extract Fields With Awk

```bash
awk -F: '{print $1}' /etc/passwd
```

`-F:` splits each line at colons. Awk's `$1` selects the first field; single quotes stop the shell expanding it. These are local account names, not a complete classroom roster.

Change `$1` to `$7` to inspect shell paths, like the fields used in your report.

Checkpoint: use the checkpoint routine with `guide now` before vim.

<!-- end_slide -->

# Create A File In Vim

```bash
mkdir -p ~/playground
vim ~/playground/vim-note.txt
```

For a new file, press `i`, type `My timer rebuilds existing site source.`, press Esc, type `:wq`, and press Enter. If the file already exists, keep its notes and add your sentence.

Back at the shell, run `cat ~/playground/vim-note.txt`. Esc then `:q!` and Enter quits without saving; `:w` saves without quitting.

Checkpoint: use the checkpoint routine with `guide now` before the README.

<!-- end_slide -->

# Write The README

```bash
micro ~/src/README.md
```

Explain the site, both public URLs, report generation, build, service, logs, and recovery. Save with `Ctrl-S` and quit with `Ctrl-Q`; the source handoff and Git steps follow after the webring.

Checkpoint: use the checkpoint routine with `guide now` before the webring.

<!-- end_slide -->

# Enable The Webring

Set `webring = true` in source, not generated HTML:

```bash
micro ~/src/site.toml
build-website
grep -i webring ~/public_html/index.html
build-website
grep -i webring ~/public_html/index.html
```

Open the homepage in your laptop browser after each build; keep one set of navigation links.

Checkpoint: use the checkpoint routine with `guide now` before the source handoff.

<!-- end_slide -->

# Preserve The Working Project

Follow [Prepare a source handoff](../../quests/prepare-source-handoff.md) now:

- Copy `maker-report.sh`, `site-check.sh`, and `site.sh` into `~/src/scripts/`.
- Copy `site.service`, `site-build.service`, and `site-build.timer` into `~/src/services/`.
- Keep active originals in place. Inspect before replacing an existing copy.
- Use the S4 Git workflow: inspect, stage only these files and README/source changes, commit, push, then verify them in Forgejo.

A Git log listing is not a backup of files outside the repo.

Final checkpoint: use the checkpoint routine with `guide now`. Once all seven core steps are complete, it shows your current quest. Remaining quests are optional reinforcement.

<!-- end_slide -->

# Exit Goal

You created a working timer, ran both text transforms, saved a vim note, and published a documented project with a webring and recoverable scripts and units.

<!-- end_slide -->

# Before S10

S10 is on **2026-10-24**: Bandit teamwork, your site demo, and next steps.

Finish any missing core work with the self-study guide. Rehearse the [demo](../../quests/demo-site.md), including the local backend and both public URLs.

Optional: [try cron and remove only your demo job](../../quests/try-cron-and-remove-it.md), or refresh pipelines for Bandit.

Run `guide now` for your current session objective; after you complete it, it shows your current quest. Submit prompted answers with `guide answer 'your answer'`, and use the same checkpoint routine after practice. Optional quest completion is not a graduation prerequisite.
