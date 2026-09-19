# Prepare a source handoff

Quest: prepare-source-handoff

## Mission

Preserve the existing site source, peer-tested operations README, two scripts, and three systemd units in `~/src`. Push and verify the actual files so the project can be restored, not merely described.

## Before You Start

Use your own classroom account. Run `git -C ~/src status`; if this is not a repository, recover through the [S4 Git workflow](../sessions/S04/self-study.md#git-workflow). Do not replace the site or initialize a second project.

Pause the timer and inspect the build state:

```bash
systemctl --user stop site-build.timer
systemctl --user status site-build.service --no-pager
```

If the service is still `activating`, wait for completion and inspect again. Do not stop a build mid-publication. Let any terminal build finish too, and keep automation paused until the copies and commit are complete: report refreshes change tracked source. An inactive successful oneshot is normal; a failed one needs its journal inspected.

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

## Document And Peer-Test Recovery

Complete [Write your README](write-readme.md). Include these paths, dependencies, both actual public links, the report/refresh/build distinction, timer control, service/log commands, and recovery instructions below. Keep the site's existing pages, package manifests, lockfile, app files, and configuration tracked too; five copied files alone are not the whole site.

The report generator must preserve the last valid report on failure and return nonzero. Follow [S9 report preparation](../sessions/S09/self-study.md#report-safety-gate) when updating an older copy. Preserve the working temporary-file version, not a stale direct-write copy.

Test the README with a peer directing and the owner operating their own account. Verify a refresh/build and an agreed brief web-service stop/recovery. Swap roles, not passwords. Write down the ambiguity fixed and actual recovery evidence.

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

This personal Caddy serves plain HTTP; shared Caddy is a separate process handling public HTTPS and proxying to `127.0.0.1` at the assigned port. Do not add `--domain`. No Caddy configuration file is needed. `file-server` disables the admin API, so use `systemctl --user` rather than `caddy stop` or `caddy reload`, which might target the shared process. `--access-log` supplies structured request fields (`request.method`, `request.uri`, `status`, and `ts` in JSON) to the journal. A missing index returns `404` with browsing disabled even if the unit is active.

The restored `site-build.service` must have the [report pre-start and npm build](../sessions/S09/self-study.md#timer-files). Confirm its npm executable path matches the installed `/usr/local/bin/npm`; a command found on interactive `PATH` alone does not prove a unit's absolute path works. Leave its timer stopped while installing the trusted project's locked dependencies and building once:

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

Restore the [hourly timer](../sessions/S09/self-study.md#hourly-schedule), removing classroom timing directives, reloading while stopped, and enabling/starting it. Inspect its next deadline and `loginctl show-user "$USER" -p Linger`; staff owns lingering policy. After any restoration adaptations, copy the working versions back into `~/src` deliberately and preserve those changes in Git.

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

When finished, restart the already-reviewed hourly timer:

```bash
systemctl --user start site-build.timer
systemctl --user list-timers --all site-build.timer
```

Report Markdown may become modified again after the next automatic refresh; that is not proof your push failed. Commit deliberate snapshots, not every timer run. Keep working copies and tracked copies synchronized after future script or unit edits.

## Related Reading

- [Git status](../commands/git-status.md)
- [Git basics](../concepts/git-basics.md)
- [S9 self-study](../sessions/S09/self-study.md)
