# S9 Self-Study Guide: Timers, Text, Polish

Session: S9

## Study Path

1. Try cron safely and remove the temporary job.
2. Build a user systemd timer for site rebuilds.
3. Use `sed` for one substitution and `awk` for one field extraction.
4. Survive vim: insert, escape, save, quit.
5. Write a README that explains the site, build, service, and recovery path.
6. Enable the webring through source configuration, then rebuild.
7. Refresh pipes and redirection for Bandit.

## Safe Cron Workflow

Do not use `crontab -r` for this practice.

```bash
crontab -l > ~/crontab.backup 2>/dev/null || true
printf '%s\n' "$HOME"
EDITOR=micro crontab -e
crontab -l
cat ~/cron.log
```

Use an absolute path in the cron line:

```text
* * * * * date >> /home/username/cron.log 2>&1
```

Remove only that one line with `EDITOR=micro crontab -e`, then verify with `crontab -l`. If the wrong editor opens and you are stuck in vim, press Esc, type `:q!`, and press Enter.

If you damage the crontab, inspect the backup before restoring it:

```bash
cat ~/crontab.backup
crontab ~/crontab.backup
```

Do not restore blindly if the backup contains old jobs you do not understand.

## Timer Files

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
Persistent=true

[Install]
WantedBy=timers.target
```

Lifecycle:

```bash
systemctl --user daemon-reload
systemctl --user enable --now site-build.timer
systemctl --user list-timers
systemctl --user start site-build.service
journalctl --user -u site-build.service --no-pager -n 50
```

## Text Transform Anatomy

```bash
printf '# heading\n' | sed 's/^# \(.*\)$/<h1>\1<\/h1>/'
awk -F: '{print $1}' /etc/passwd
```

These are text-transform one-liners. Sed substitutes text. Awk splits records into fields. Single quotes protect `$1` from the shell. In the sed pattern, `^`, `$`, `.*`, and the capture group are regular expression pieces.

## README Minimum

Include: purpose, public URL, build command, service command, logs command, project structure, and recovery notes.

## Webring Source Setting

Enable the webring in source configuration, not generated HTML:

```bash
micro ~/src/site.toml
build-website
grep -i webring ~/public_html/index.html
```

The setting must be `webring = true`. Re-run `build-website` twice and confirm the output still has one clean set of navigation links.

## Bandit Warmup

For each level, keep the loop small:

```bash
ls -la
cat README 2>/dev/null || true
find . -maxdepth 2 -type f
```

Read the level goal, inspect files, try one command, then write down what worked. S10 starts from this method, not from memorized answers.

## Troubleshooting

- Cron did nothing: use absolute paths and inspect `~/cron.log`.
- Timer did nothing: run `systemctl --user list-timers` and start the paired service manually.
- Sed output is unchanged: test the regular expression against one known input line.
- Vim feels stuck: press Esc, type `:q!`, and press Enter.

## Proof Checklist

- `~/cron.log` has date lines and the cron job has been removed.
- `site-build.timer` appears in `systemctl --user list-timers`.
- You can explain the sed capture group and awk field separator.
- README exists, is committed, and explains how to run or recover the site.
- Generated HTML contains webring navigation after two rebuilds, without duplicate output.

## Docs Pointers

- Run `man 5 crontab`, `man sed`, `man awk`, and `man vim`.
- Read [systemd timer units](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html).
- For webring work, follow [enable-webring](../../quests/enable-webring.md) and use the exact `webring = true` setting.
- Read [Regular Expression](../../concepts/regular-expression.md) before changing sed patterns.
- Read the [GNU sed manual](https://www.gnu.org/software/sed/manual/sed.html) and [GNU awk manual](https://www.gnu.org/software/gawk/manual/gawk.html) when the one-liners stop being enough.
- Read [One-Liners](../../concepts/oneliner.md) before compressing timer checks, text transforms, and publishing commands into one prompt line.
