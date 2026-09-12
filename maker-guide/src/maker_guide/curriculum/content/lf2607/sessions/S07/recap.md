# S7 Recap: Your page on the wire

Session: S7

## Core Idea

S6 checked whether your existing pages respond. S7 compares what you build with what HTTP carries, constructs a raw request, and separates static-file serving from a personal backend route.

## Remember

- Reuse `bash ~/scripts/site-check.sh "" maker-report.html` unchanged for static preflight. These arguments select the homepage and report on one host.
- `curl -I` reuses S6's `HEAD` request: headers, no page body. `GET` fetches the body.
- Compare `~/public_html/index.html` with the successfully fetched body, not with response headers. `diff` prints nothing and exits `0` for identical files; `1` means differences and `2` means an error. These files should match: investigate any mismatch, rebuild, and refetch.
- Markdown source and generated HTML are related, not identical. Edit source and rebuild; do not repair generated HTML by hand.
- `curl -v` exposes connection/TLS details and request/response headers. The user subdomain is a separate service route, not S6's report path.
- With routing working, the service route normally returns `502` before S8 because no backend is listening. A DNS or TLS failure is not an HTTP status. Report what you actually observe.
- Raw `nc` to the existing plaintext loopback Caddy port `80` normally gets an HTTPS `308`/`3xx` redirect, not the homepage HTML. `nc` does not follow redirects or speak TLS on port `443`.
- The raw HTTP/1.1 request needs its request line, `Host`, CRLF line endings, and final blank line. `Connection: close` asks the server to close; `-w 3` bounds connection and idle waits.

## Live Core

All four guide objectives are required core work:

1. Inspect static response headers with `curl -I`.
2. Run `build-website`, fetch a body, and use `diff` to compare it with generated HTML.
3. Inspect the service subdomain with `curl -v` and explain the result.
4. Create headed `~/src/pages/setup.md`, link `setup.html` from `index.md`, rebuild, and verify the generated page and browser navigation.

Also explain the raw request and its observed redirect. Inspect real results yourself, because the guide does not independently verify HTTP success or body equality.

Checkpoint routine: run `guide now` before starting a quest and after practical work. It checks one task and shows the next on success; otherwise follow the feedback. Use `guide answer 'your own observation'` when asked; `guide check` is an optional explicit check. Use this for all four core tasks, including setup once its files, link, and build are ready.

## Optional Reinforcement

After the core, the S7 quests offer more site and HTTP practice. ASCII art, troubleshooting notes, and the [closed-port probe](../../quests/probe-closed-port.md) are optional reinforcement. Use `guide now`, submit prompted observations with `guide answer 'your own observation'`, then follow the checkpoint routine.

## Can You Explain This?

- What is the difference between source Markdown and generated HTML?
- What does `curl -I` omit?
- Why does the raw port-80 request return a redirect rather than your generated page?
- Why is the service subdomain not just another path checked by `site-check.sh`?
- Why can a proxy return an error when the HTML files are fine?

## Keep

Keep `setup.md`, its homepage link, and rebuilt `setup.html`. Keep your existing report and unchanged `site-check.sh`. `art.md` and troubleshooting notes are optional demo polish.

## Full Autonomy

Use [S7 Self-Study Guide: Your page on the wire](self-study.md) for executable activities, the complete bounded raw request, route diagnosis, and setup-page instructions.

## Next Session

S8: 2026-09-26, your own web service. Run your own backend and manage its lifecycle: start, stop, restart, inspect logs, and keep it running after logout.
