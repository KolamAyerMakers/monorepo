# Add uptime to the report

Quest: extend-maker-report

## Mission

Add a labeled `uptime` line to `maker-report.sh`, regenerate `~/src/pages/maker-report.md`, and rebuild the site.

## Commands You Will Use

- `micro`
- `uptime`
- `cat`
- `build-website`

## Steps

1. Run `guide now` so this quest is assigned before you create evidence.
2. Run `uptime` by itself and inspect its output.
3. Open `~/scripts/maker-report.sh` in Micro.
4. Inside the report group, after the date lines, print the label `* Uptime: ` and run `uptime` on the next line.
5. Run `~/scripts/maker-report.sh "Uptime Report"`. The script rewrites `~/src/pages/maker-report.md`.
6. Inspect the Markdown with `cat ~/src/pages/maker-report.md`, then run `build-website`.
7. Open the report page and run `guide check`.

## Hints

1. Follow the same two-line shape as the existing User, Host, and Date entries.
2. The `uptime` command already writes a final newline.
3. The script, Markdown source, and built HTML all need the labeled uptime value.

## If Check Fails

Run `bash -x ~/scripts/maker-report.sh "Uptime Report"`. The trace remains visible while report output goes to the Markdown file. Confirm the file contains one line beginning `* Uptime: `, then rebuild before checking again.

## Related Reading

- [`uptime`](../commands/uptime.md)
- [Shell Scripting](../concepts/shell-scripting.md)
- [Filesystem As CMS](../concepts/filesystem-as-cms.md)
