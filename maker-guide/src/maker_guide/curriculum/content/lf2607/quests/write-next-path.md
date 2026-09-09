# Write the next path

Quest: write-next-path

## Mission

Create and publish `~/src/pages/next.md` with one dated Linux next action after S10. Publish this page alongside your final site demo.

## Commands You Will Use

- `micro`
- `build-website`
- `git add`
- `git commit`
- `git push`

## Write The Page

Work in your classroom shell, not on Bandit or in a laptop directory with the same name. Run `micro ~/src/pages/next.md`, inspect any existing page, and adapt this Markdown:

```markdown
# My Next Linux Project

Path: Maintain my Linux site and service.

Next action: On 2026-10-31, rebuild my site, run my checker, and inspect service logs.

Risk: A source change could break a page.

Recovery plan: Review the last working commit and rebuild that version.

Documentation: [systemd service units](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html).

Proof: Both public URLs respond and the updated page is visible.
```

Keep a real Markdown heading containing Linux and an explicit `Next action:` line with an action and date. Use your own plan rather than publishing an empty template.

## Link And Publish

Edit `~/src/pages/index.md` without replacing existing content, adding a link such as:

```markdown
[My next Linux project](next.html)
```

Inspect the new page with Micro too: `git diff` does not show untracked file contents. If unrelated work is already staged, stop and resolve that selection before committing. If the repo or remote is missing, return to the [S4 Git and Forgejo workflow](../sessions/S04/self-study.md#git-workflow), not a new project.

Then build and use the existing S4 Git workflow:

```bash
build-website
curl -I "https://lf2607.kolamayermakers.org/~$USER/next.html"
cd ~/src
git status
git diff -- pages/next.md pages/index.md
git add -- pages/next.md pages/index.md
git diff --cached
git status
git commit -m "Write next Linux step"
git push
```

Open the homepage link and next page in your laptop browser, then verify the commit in Forgejo. Run `guide check` in the classroom when this quest is current. After graduation, carry out the dated action and update its proof.

## Hints

1. Choose one real next path, not five vague wishes.
2. A heading starts with `# `, not a plain `Path:` label.
3. `Next action:` makes the commitment easy to find; include a documentation link you will actually use.

## If Check Fails

Inspect `~/src/pages/next.md` for a Markdown heading containing Linux and a non-empty `Next action:` line with a real action and date. Check the generated `~/public_html/next.html`, homepage link, and pushed commit.

## Related Reading

- [multi-page sites](../concepts/multi-page-sites.md)
- [README writing](../concepts/readme-writing.md)
