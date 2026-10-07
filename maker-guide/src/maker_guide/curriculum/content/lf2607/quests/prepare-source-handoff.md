# Prepare a source handoff

Quest: prepare-source-handoff

> **Historical guide:** this quest documents an earlier project version and is not the current S9 handoff route. Its report-refresh and Git steps are not requirements for the current daily-pick project. For current setup, follow [S9 daily-build instructions](../sessions/S09/self-study.md) and the [daily-pick quest](schedule-site-rebuilds.md). Restoring files from this guide does not restore the current daily-pick generator; use the current S9 instructions to set that up.

## Mission

Preserve the existing site source, personal README notes, two scripts, and three systemd units in `~/src`. Push and verify the actual files so the project can be restored, not merely described.

## Before You Start

Use your own classroom account. Run `git -C ~/src status`; if this is not a repository, recover through the [S4 Git workflow](../sessions/S04/self-study.md#git-workflow). Do not replace the site or initialize a second project.

Pause the timer and inspect the build state:

```bash
systemctl --user stop site-build.timer
systemctl --user status site-build.service --no-pager
```

If the service is still `activating`, wait for completion and inspect again. Do not stop a build mid-publication. Let any terminal build finish too. An inactive successful oneshot is normal; a failed one needs its journal inspected.

## Copy Working Files

Keep active originals where they run. Copy, do not move:

| Working Original | Versioned Copy |
|---|---|
| `~/scripts/maker-report.sh` | `~/src/scripts/maker-report.sh` |
| `~/scripts/site-check.sh` | `~/src/scripts/site-check.sh` |
| `~/.config/systemd/user/site.service` | `~/src/services/site.service` |
| `~/.config/systemd/user/site-build.service` | `~/src/services/site-build.service` |
| `~/.config/systemd/user/site-build.timer` | `~/src/services/site-build.timer` |

```bash
mkdir -p ~/src/scripts ~/src/services
cp -iv ~/scripts/maker-report.sh ~/scripts/site-check.sh ~/src/scripts/
cp -iv ~/.config/systemd/user/site.service ~/.config/systemd/user/site-build.service ~/.config/systemd/user/site-build.timer ~/src/services/
ls -l ~/src/scripts ~/src/services
```

`cp -i` asks before overwriting; `-v` identifies copies. At a replacement prompt, answer `n` first and inspect both versions. For example:

```bash
diff -u ~/src/scripts/maker-report.sh ~/scripts/maker-report.sh
```

No output means equal contents. Differences require a decision before repeating the copy and answering `y`. Repeat for every conflicting copy; never replace newer source blindly. Preserve executable permissions on scripts used directly. Do not include credentials, private keys, tokens, dependency directories, or generated HTML in the handoff.

## Keep Personal Notes

Use [Write your README](write-readme.md) for brief personal operating notes. Keep the site's existing pages, package manifests, lockfile, app files, and configuration tracked too; five copied files alone are not the whole site.

If preserving an existing system-report page, use the current [provided report script](../sessions/S06/self-study.md#provided-report-script) and preserve any personal additions before replacing it.

## Restore From Source

These are recovery instructions, not a reason to overwrite today's working project. On a replacement account, obtain the trusted repository as `~/src` using the [S4 Forgejo workflow](../sessions/S04/self-study.md#forgejo-remote). If `~/src` already exists, inspect and reconcile it rather than cloning over it. The classroom supplies Bash, Caddy, Node/npm, Pandoc, and publishing tools; review the project's package scripts and README for its actual requirements before executing them. On another host, arrange missing dependencies and routing with its operator first.

Pause any existing build timer and wait for active builds as above. `Unit ... not found` is expected only on a fresh account. Inspect before replacing working files:

```bash
mkdir -p ~/scripts ~/.config/systemd/user
cp -iv ~/src/scripts/maker-report.sh ~/src/scripts/site-check.sh ~/scripts/
cp -iv ~/src/services/site.service ~/src/services/site-build.service ~/src/services/site-build.timer ~/.config/systemd/user/
chmod u+x ~/scripts/maker-report.sh ~/scripts/site-check.sh
printf '%s\n' "$((10000 + $(id -u)))"
command -v caddy npm
/usr/bin/caddy version
/usr/local/bin/npm --version
micro ~/.config/systemd/user/site.service
```

At overwrite prompts, inspect conflicting versions before accepting. Review all three copied units, including drop-ins shown by `systemctl --user cat`, and adapt executable paths and classroom hostnames where necessary. If the computed port exceeds `65535`, stop and ask staff. In `site.service`, replace `12345` below with your printed numeric port, not a shell expression:

```ini
[Unit]
Description=Personal website service

[Service]
WorkingDirectory=%h
ExecStart=/usr/bin/caddy file-server --listen :12345 --root %h/public_html --access-log
Restart=on-failure

[Install]
WantedBy=default.target
```

The working directory is the stable home directory. `--root` resolves the current published tree as requests arrive; it avoids holding the old directory after the publisher swaps `public_html`. Keep the explicit root: do not expose the home directory. The listener uses all interfaces; the classroom firewall blocks new direct external connections to the assigned port. On another host, have its operator confirm equivalent protection before using this listener. Caddy follows symlinks, so the root is not a filesystem sandbox. Systemd does not evaluate Bash assignments or shell arithmetic here; use the literal numeric port, not `$PORT`.

This personal Caddy serves plain HTTP; shared Caddy is a separate process handling public HTTPS and proxying to `127.0.0.1` at the assigned port. Do not add `--domain`. No Caddy configuration file is needed. Use `systemctl --user` rather than `caddy stop` or `caddy reload`, which might target the shared process. `--access-log` supplies structured request fields (`request.method`, `request.uri`, `status`, and `ts` in JSON) to the journal. A missing index returns `404` with browsing disabled even if the unit is active.

Historical version: the restored `site-build.service` used a report pre-start and npm build. That retired setup is not the current S9 configuration; consult the current S9 instructions linked above before configuring or starting today's build. For this earlier version, confirm its npm executable path matches the installed `/usr/local/bin/npm`; a command found on interactive `PATH` alone does not prove a unit's absolute path works. Leave its timer stopped while installing the trusted project's locked dependencies and building once:

```bash
cd ~/src
npm ci
systemctl --user daemon-reload
systemctl --user start site-build.service
journalctl --user -u site-build.service --no-pager -n 50
```

Run one command at a time and stop on installation, report, or build errors. Do not start serving a failed restoration or enable repeated failed builds. Check the generated homepage and report exist before continuing. Stop any manual server you own in its own terminal before starting systemd on the same port; never kill an unknown process.

```bash
ls -l ~/public_html/index.html ~/public_html/maker-report.html
systemctl --user enable site.service
systemctl --user restart site.service
systemctl --user status site.service --no-pager
service_port="$((10000 + $(id -u)))"
curl --max-time 10 -fsS "http://127.0.0.1:$service_port/maker-report.html"
curl --max-time 10 -fsS "https://$USER.lf2607.kolamayermakers.org/maker-report.html"
bash ~/scripts/site-check.sh "" maker-report.html
```

`restart` starts a stopped service too and applies changed configuration to one already running. `daemon-reload` alone does not restart it. If a previous failure hit a start limit, fix the cause, run `systemctl --user reset-failed site.service`, then retry the restart. Inspect the journal and actual response bodies, and open both public routes from your laptop. Do not bypass TLS or change shared routing to make an error disappear.

For this earlier version, restore the daily 09:00 calendar timer and remove any temporary test interval before reloading and starting it. For today's project, follow the current S9 timer setup linked above. Inspect its next deadline and `loginctl show-user "$USER" -p Linger`; staff owns lingering policy.

## Inspect, Commit, Push

Keep the timer stopped and builds finished during this sequence. Read new files with Micro or `cat`: `git diff` does not show untracked contents. Run `git diff --cached` before staging too; if unrelated files are already staged, stop and resolve the selection with their owner rather than committing or discarding them.

```bash
cd ~/src
git status
git diff
git diff --cached
git add -- README.md pages/maker-report.md
git add -- scripts/maker-report.sh scripts/site-check.sh
git add -- services/site.service services/site-build.service services/site-build.timer
git diff --cached
git status
git commit -m "Preserve site operations and source handoff"
git remote -v
git push
git log --oneline -3
git status
```

Inspect and stage any other intended site source changes by their explicit paths, not with broad staging. Only commit when the staged diff contains exactly what you intend and no secrets. If the remote or upstream is missing, use the [S4 Forgejo steps](../sessions/S04/self-study.md#forgejo-remote). Resolve a rejected push by inspecting the remote work with staff; do not force-push.

Open the repository in Forgejo from your laptop. Verify the newest commit, README, report/site source, both scripts, and all three units. A local commit or successful command alone is not verification of the remote file contents.

When finished with this earlier version, restore its daily 09:00 schedule, then restart its timer. For today's project, use the current S9 timer instructions linked above:

```bash
systemctl --user stop site-build.timer
systemctl --user daemon-reload
systemctl --user start site-build.timer
systemctl --user list-timers --all site-build.timer
```

In the earlier version, report Markdown could change after an automatic refresh; that was not proof a push failed. Commit deliberate snapshots, not every timer run. Keep working copies and tracked copies synchronized after future script or unit edits.

## Related Reading

- [Git status](../commands/git-status.md)
- [Git basics](../concepts/git-basics.md)
- [S9 self-study](../sessions/S09/self-study.md)
