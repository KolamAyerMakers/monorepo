# Prepare a source handoff

Quest: prepare-source-handoff

## Mission

Preserve your working project in the existing `~/src` repository, including scripts and systemd units that currently live outside it. Push the files so another person can recover the site from source.

## Commands You Will Use

- `cp`
- `git add`
- `git commit`
- `git push`
- `git log`
- `git status`

## Before You Start

Run `git -C ~/src status`. If it is not a repository, complete the [S4 Git workflow](../sessions/S04/self-study.md#git-workflow) first. Do not create a second project or replace your site. Use the working report/checker from S5/S6, helper/service from S8, and build units from S9.

## Copy Working Files

Keep the active originals at their current paths. Copy, do not move:

| Working Original | Versioned Copy |
|---|---|
| `~/scripts/maker-report.sh` | `~/src/scripts/maker-report.sh` |
| `~/scripts/site-check.sh` | `~/src/scripts/site-check.sh` |
| `~/bin/site.sh` | `~/src/scripts/site.sh` |
| `~/.config/systemd/user/site.service` | `~/src/services/site.service` |
| `~/.config/systemd/user/site-build.service` | `~/src/services/site-build.service` |
| `~/.config/systemd/user/site-build.timer` | `~/src/services/site-build.timer` |

`cp -i` asks before overwriting; `-v` shows what was copied. If prompted, answer `n` first and inspect both versions before deciding what to keep.

```bash
mkdir -p ~/src/scripts ~/src/services
cp -iv ~/scripts/maker-report.sh ~/scripts/site-check.sh ~/src/scripts/
cp -iv ~/bin/site.sh ~/src/scripts/site.sh
cp -iv ~/.config/systemd/user/site.service ~/.config/systemd/user/site-build.service ~/.config/systemd/user/site-build.timer ~/src/services/
ls -l ~/src/scripts ~/src/services
```

For example, compare an existing report-script copy with the working original:

```bash
diff -u ~/src/scripts/maker-report.sh ~/scripts/maker-report.sh
```

No diff output means they match. If they differ, decide which changes to keep before rerunning that copy and answering `y`. Repeat for any other existing copy. Do not silently replace a previously committed script with an older working copy, and do not copy passwords, tokens, or keys into the repo.

## Hints

- Preserve the actual working files, including those outside the repository.
- Inspect conflicting copies before overwriting and keep active originals in place.
- The guide checks committed local copies. Verify the push and the contents in Forgejo yourself.

## Document Recovery

Edit `~/src/README.md`, keeping useful existing text. Include a Markdown title, the site's purpose, both public links, build/run/log commands, and the path table above. Use your actual username in links; `$USER` does not expand inside Markdown.

Explain the recovery order: obtain the source as `~/src`, install its required tools/dependencies, copy scripts and units back to their working paths with overwrite prompts, restore executable permissions where needed, build, reload user systemd, then enable `site.service` and `site-build.timer`. On another machine, review the numeric port in `site.service`, installed executable paths, and hostnames before starting anything. The classroom port is `10000 + uid`, which `~/bin/site.sh site_port` prints.

Record that `maker-report.sh` collects facts into `~/src/pages/maker-report.md`; the build only renders that existing Markdown. Keep the report page and other site source in the same repository. Do not rely on local `.backup` files or automatic source commits to preserve files outside `~/src`, especially systemd units.

## Inspect, Commit, Push

Reuse the S4 workflow. Review the report page and new copies with `cat` or Micro as well as `git diff`, which does not show untracked file contents. Check script permissions with `ls -l`; the report script and helper should retain their execute permission. Stop if unrelated files are already staged; resolve that selection before committing.

```bash
cd ~/src
git status
git diff
git add -- README.md site.toml pages/maker-report.md
git add -- scripts/maker-report.sh scripts/site-check.sh scripts/site.sh
git add -- services/site.service services/site-build.service services/site-build.timer
git diff --cached
git status
git commit -m "Preserve site scripts and services"
git remote -v
git push
git log --oneline -3
git status
```

For any other intended page change, inspect and stage its exact path in a deliberate commit; do not use broad staging. If `origin` or its upstream is missing, follow the [S4 Forgejo steps](../sessions/S04/self-study.md#forgejo-remote), not a second `git init`.

Open your Forgejo repository from your laptop. Verify the newest commit, README, report source, all three scripts, and all three units there. A local commit is not yet an off-machine copy.

## If Check Fails

Inspect the six versioned copies and README, and confirm the commit is visible in Forgejo. A missing original is earlier project work to recover, not an empty file to create for the check. Keep the active scripts and units working after the copy.

## Related Reading

- [git log](../commands/git-log.md)
- [git status](../commands/git-status.md)
- [git basics](../concepts/git-basics.md)
- [S9 self-study](../sessions/S09/self-study.md)
