# Publish a network fetch

Quest: publish-network-fetch

## Mission

Create `~/scripts/fetch-status.sh` that writes a fetched HTTP result to `~/src/pages/network.md`, then rebuilds the site.

## Commands You Will Use

- `bash`
- `curl`
- `date`
- `printf`
- `micro`
- `build-website`

## Before You Start

Confirm these paths exist:

```bash
ls -ld ~/scripts ~/src/pages
```

If `~/scripts` is missing, create it with `mkdir -p ~/scripts`. If `~/src/pages` is missing, return to the site setup material before doing this quest.

## Steps

1. Create `~/scripts/fetch-status.sh`.
2. Use the fetched content pattern from [S6 self-study](../sessions/S06/self-study.md).
3. Write a Markdown heading `# Network Fetch`.
4. Write the current date.
5. Write fetched output from `curl -L https://example.org` inside a fenced `text` block.
6. Write the result to `~/src/pages/network.md`.
7. Run `build-website`.
8. Ask the guide to check the source file.

## Minimal Script Shape

```bash
#!/bin/bash
set -euo pipefail

{
  printf '# Network Fetch\n\n'
  printf 'Fetched at: '
  date
  printf '\n```text\n'
  curl -L https://example.org
  printf '\n```\n'
} > "$HOME/src/pages/network.md"

build-website
```

## Expected Output

`~/src/pages/network.md` should contain a heading, a timestamp, and an HTML document from `example.org` inside a fenced text block.

## Hints

1. `curl -L` follows redirects.
2. The braces group output so one redirection can write the whole Markdown file.
3. The check looks for a heading and fenced text block.

## If Check Fails

- If `curl` fails, run `curl -I https://example.org` and read the status line.
- If `network.md` is empty, run the script with `bash ~/scripts/fetch-status.sh` and read the first error.
- If the page did not publish, run `build-website` again and inspect `~/public_html/network.html`.
- If the fenced block is broken, make sure both opening and closing triple backticks exist.

## Related Reading

- [curl](../commands/curl.md)
- [date](../commands/date.md)
- [external-data-fetching](../concepts/external-data-fetching.md)
- [S06 self-study](../sessions/S06/self-study.md)
- [curl manual](https://curl.se/docs/manpage.html)
