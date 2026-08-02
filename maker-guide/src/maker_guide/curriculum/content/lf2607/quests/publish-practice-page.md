# Publish a practice page

Quest: publish-practice-page

## Mission

Create `~/src/pages/practice.md` with a fenced block of recent command history.

## Commands You Will Use

- `history`
- `tail`
- `tee`
- `micro`
- `build-website`

## Steps

1. Create `~/src/pages/practice.md`.
2. Add the heading `# What I ran this week`.
3. Add a fenced code block with recent `history | tail -30` output.
4. Run `build-website`.
5. Ask the guide to check the source file.

## Hints

1. Markdown fenced code blocks use triple backticks.
2. Save source under `~/src/pages/`, not directly under `~/public_html/`.
3. The heading and fence are both required.

## If Check Fails

Open the file again and make sure it has the heading plus opening and closing triple backticks.

## Related Reading

- [tee](../commands/tee.md)
- [filesystem-as-cms](../concepts/filesystem-as-cms.md)
