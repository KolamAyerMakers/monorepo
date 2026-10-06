# Write your README

Quest: write-readme

## Mission

Write short personal notes that help you understand and operate your existing site, then preserve them with the source handoff.

## Write For The Next Operator

Open `micro ~/src/README.md`, keeping useful existing content. Save with `Ctrl-S` and quit with `Ctrl-Q`. Include:

- A heading and short description of your site.
- Useful source/output paths and actual public links.
- The refresh and build command, how to pause/resume the timer, and commands to inspect your service and logs.
- Keep useful existing notes; use the [source handoff guide](prepare-source-handoff.md) for copying and restoration details.

Use [S9 self-study](../sessions/S09/self-study.md) for runnable automation instructions. Explain commands in your own project's README rather than leaving only vague words such as "build" or "fix".

## Preserve The Result

Follow [Prepare a source handoff](prepare-source-handoff.md#inspect-commit-push): pause and wait, inspect all intended files, stage explicit paths, commit, push, and verify the README and working-file copies in Forgejo. A readable local README alone is not a recoverable off-machine handoff.

## Related Reading

- [README writing](../concepts/readme-writing.md)
- [Forgejo publishing](../concepts/forgejo-publishing.md)
