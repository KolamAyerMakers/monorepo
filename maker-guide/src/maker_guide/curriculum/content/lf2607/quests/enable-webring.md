# Enable the webring

Quest: enable-webring

## Mission

Enable the cohort webring in source configuration and verify the generated navigation.

## Commands You Will Use

- `micro`
- `build-website`
- `grep`
- `curl`

## Before You Start

This quest changes site source configuration. Do not hand-edit `~/public_html/index.html` as the permanent fix. Generated HTML must come from the build process so it survives rebuilds.

A webring is a small navigation block that links learner sites together. Your site joins the ring when the source config says `webring = true`, then `build-website` generates previous and next links in the homepage output.

## Steps

1. Open `~/src/site.toml`.
2. Add or update the line `webring = true`.
3. Run `build-website`.
4. Verify locally with `grep -i webring ~/public_html/index.html`.
5. Verify over HTTP with `curl -L https://lf2607.kolamayermakers.org/~username/ | grep -i webring`.
6. Run `build-website` again and verify the webring is still present without duplicate output.
7. Ask the guide to check generated output.

## Expected Output

The generated homepage should contain cohort navigation such as webring, previous, or next links.

## Hints

1. Source configuration beats appending fragments to generated output.
2. The exact config line is `webring = true`.
3. If output duplicates after a rebuild, something is still mutating generated HTML instead of generating it from source.

## If Check Fails

- If `grep` finds nothing locally, inspect `~/src/site.toml` and rerun `build-website`.
- If local output works but HTTP output does not, fetch with `curl -L` and confirm the URL uses your username.
- If output is duplicated, remove the append step and make the build generate the page idempotently.

## Related Reading

- [build-website](../commands/build-website.md)
- [site-source-ownership](../concepts/site-source-ownership.md)
- [S09 self-study](../sessions/S09/self-study.md)
