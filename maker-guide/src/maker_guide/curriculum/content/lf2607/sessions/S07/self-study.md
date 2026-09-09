# S7 Self-Study Guide: Your page on the wire

Session: S7

## Study Path

S6 already covered DNS, ping, statuses, `HEAD`, `GET`, bodies, redirects, and the `if`/`for` checker. Reuse that knowledge rather than starting another site or checker.

The four core objectives are:

1. Inspect your static homepage headers.
2. Rebuild and compare generated HTML with the fetched HTTP body.
3. Inspect the separate service subdomain with `curl -v` and explain the failure.
4. Create a headed `setup.md`, link it from the homepage, and rebuild.

The raw HTTP lab below shows the bytes curl normally constructs.

## Preflight

Run these commands in your personal SSH account on the classroom server, not in your laptop's local shell:

```bash
whoami
printf '%s\n' "$USER"
bash ~/scripts/site-check.sh
guide now
```

`$USER` must match `whoami`; reconnect with the correct account if not. Keep `site-check.sh` unchanged. Its two URLs are the homepage and `maker-report.html`, two paths on the same static host. Read both results; its exit code is not an overall health verdict.

If the checker or report is missing, use the [S6 self-study guide](../S06/self-study.md). Repair static failures before proceeding. Do not replace your source project or add the service URL to the checker.

Run `guide now` before each objective. When prompted for an answer, use `guide answer 'your own observation'`. The guide records command/file evidence, not independent proof that a request succeeded or that two bodies match.

Checkpoint routine: successful commands can auto-complete command-history objectives. After each task, run `guide now` first. If the task you just finished is still current, run `guide check`, then `guide now`. If the next task is already current, continue without checking that unfinished task.

## 1. Inspect Headers

```bash
curl -I --max-time 10 "https://lf2607.kolamayermakers.org/~$USER/"
```

As in S6, `-I` sends `HEAD`, returning headers without the page body. Find the actual status and `content-type`. A working homepage normally returns `200`; a redirect has a `Location` to inspect. `--max-time 10` bounds the request to ten seconds.

If redirected, use `curl -I -L --max-time 10` with the same URL to inspect the next response. Record what happened, not a fabricated `200`. Use the checkpoint routine: `guide now` first.

## 2. Compare Source, Disk, And Body

```text
~/src/pages/index.md -> build-website -> ~/public_html/index.html -> HTTP response body
```

Rebuild your existing site:

```bash
build-website
```

Stop and repair any build error before continuing. Inspect the two local views:

```bash
cat ~/src/pages/index.md
cat ~/public_html/index.html
```

Find your heading in both. The Markdown is the source you edit. Generated HTML adds tags and layout, so those two files should not be identical. Do not edit `~/public_html/index.html`; the next build replaces it.

Fetch the homepage body into your own playground, not into the source or published file:

```bash
mkdir -p ~/playground
curl -fSs --max-time 10 -o ~/playground/s7-index-from-web.html \
  "https://lf2607.kolamayermakers.org/~$USER/"
```

This sends `GET`. `-f` makes HTTP errors such as `404` fail; `-sS` hides progress but keeps errors; `-o` saves the body. Curl removes HTTP framing. Do not add `-I` (no body) or `-i` (headers mixed into the saved file).

Only after a successful fetch, compare the generated HTML with that body:

```bash
diff -u ~/public_html/index.html ~/playground/s7-index-from-web.html
```

No output and exit status `0` mean identical files. Status `1` means differences, shown with `-` and `+`; status `2` means an error, such as an unreadable file. These two HTML files should match. If curl fails, do not compare an old or partial saved body. If the body differs, verify the URL and filenames, rebuild, and fetch again without editing between steps.

Once the files match, use the checkpoint routine: `guide now` first.

## Raw HTTP/1.1 Lab

Stay on the classroom server. Use the existing Caddy plaintext listener at `127.0.0.1:80`. Loopback means this machine; the TCP connection does not leave it. If `nc` is unavailable, ask the instructor to verify the classroom tools.

Run this complete request as one command:

```bash
printf 'GET /~%s/ HTTP/1.1\r\nHost: lf2607.kolamayermakers.org\r\nConnection: close\r\n\r\n' "$USER" | nc -w 3 127.0.0.1 80
```

- The request line has method `GET`, path `/~username/`, and version `HTTP/1.1`. `printf` inserts `$USER` at `%s`.
- `Host: lf2607.kolamayermakers.org` selects the hostname at Caddy. Connecting to `127.0.0.1` alone does not supply that HTTP header.
- `\r\n` is carriage return plus line feed (CRLF), the HTTP/1.1 line ending. `printf` turns those escapes into bytes.
- The final `\r\n\r\n` ends the last header and adds a blank line to finish the headers. This `GET` request has no body. Missing that blank line can leave the server waiting for more headers.
- `Connection: close` asks the server to close the connection after its response.
- `nc -w 3` limits connection and idle waits to three seconds. It is a timeout, not an HTTP status or a strict total-duration limit while data keeps arriving. `Ctrl-C` cancels.

Read the response's first line and headers. Caddy normally responds with `HTTP/1.1 308 Permanent Redirect` and an HTTPS `Location` for your path. This is the HTTP-to-HTTPS `3xx` redirect you saw in S6, not a `200` HTML response. Any redirect body is not the generated homepage. Identify the real status and destination; if the server differs, report the actual output.

`nc` neither follows redirects nor negotiates TLS. Sending plaintext to port `443` cannot make an HTTPS request. Use curl for the encrypted follow-up:

```bash
curl -I --max-time 10 "https://lf2607.kolamayermakers.org/~$USER/"
```

Compare this status with the plaintext response. Do not change Caddy, open a port, start a server, or use `curl -k` to make the exercise appear successful. If the raw exchange is refused, times out, or returns an unexpected status, keep that evidence and ask the instructor.

## 3. Inspect The Service Route

S6 compared two paths on one static host. S7 contrasts two kinds of route:

```text
https://lf2607.kolamayermakers.org/~username/ -> Caddy -> public_html/index.html
https://username.lf2607.kolamayermakers.org/  -> Caddy -> personal backend process
```

The guide may call these the "first URL" and "second URL". Here "second URL" means the user subdomain, not the `maker-report.html` path from S6. Even when hostnames reach the same machine, Caddy can route them differently.

```bash
curl -v --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
```

Read `*` connection and TLS details, `>` request headers, and `<` response headers. Verbose diagnostics go to stderr; the response body goes to stdout.

With DNS, TLS, and the proxy route working, expect `502` before S8: Caddy cannot get a usable upstream response because no personal backend service is listening yet. The static files can be fine at the same time. Rebuilding them does not start a backend.

A DNS, connection, or certificate error happens before an HTTP response and is not a `502`. If you see that, another status, or a working service, report the actual evidence and ask the instructor about the route. Do not invent a missing-backend observation or start/stop a service to force the expected result. Starting your backend belongs to S8.

Use the checkpoint routine: `guide now` first.

## 4. Create And Link Setup

```bash
micro ~/src/pages/setup.md
```

Improve an existing setup page instead of replacing it. For a new file, start with a heading and useful notes:

```markdown
# My Setup

I edit Markdown in ~/src/pages/ and publish with build-website.

[Back to my homepage](index.html)
```

Add your own workflow notes. This page is public: never include passwords, private keys, or tokens. Save with `Ctrl-S`, quit with `Ctrl-Q`.

```bash
micro ~/src/pages/index.md
```

Add this link without removing the existing homepage or report link:

```markdown
[My setup](setup.html)
```

Links target generated `.html` files, not Markdown sources. Rebuild, then inspect the generated page and headers:

```bash
build-website
cat ~/public_html/setup.html
curl -I --max-time 10 "https://lf2607.kolamayermakers.org/~$USER/setup.html"
```

Stop on a build failure rather than trusting old output. Open your homepage in your laptop browser, follow the setup link, and return using the homepage link. Terminal checks from the server do not prove access from outside. Once the heading, link, build, and generated output are present, use the checkpoint routine: `guide now` first. Check the completed setup task only if it remains current.

## Troubleshooting

- Static page is `404`: inspect the matching source, run `build-website`, and check the generated filename. Do not confuse this with a missing backend.
- `diff` differs: compare the same page, ensure the fetch succeeded, and rebuild/refetch. Headers, an error body, or a redirect body are not the generated HTML.
- Raw HTTP is silent: check `Host`, the CRLF blank terminator, and port `80`. Let the timeout finish or cancel with `Ctrl-C`; bring the exact command and output to the instructor.
- Raw HTTP is `308`: expected HTTPS redirection, not a broken page. Read `Location`; use curl for HTTPS.
- Service URL is `502`: expected with a working proxy route but no backend yet. A DNS/TLS error is a different failure, not evidence that the backend port was reached.
- Setup link is `404`: use relative `setup.html`, check spelling and case, and rebuild. Preserve all existing homepage content.

## Proof Checklist

- Identify an observed status and header from the static homepage.
- Run `build-website` and `diff` on generated HTML versus a successfully fetched body; interpret the result.
- Explain Markdown versus generated HTML, and the raw request's `Host`, CRLF terminator, close request, timeout, and redirect response.
- Run `curl -v` on the service subdomain and distinguish its missing-backend failure from static-path, DNS, or TLS errors.
- Keep a headed `setup.md`, the `setup.html` link in `index.md`, and rebuilt `~/public_html/setup.html`; follow the links in your browser.
- Complete all four core objectives using the checkpoint routine: `guide now` first.

## Optional Reinforcement

After the core, use the S7 quests to repeat page, header, and status reasoning or add ASCII art and troubleshooting notes. The [closed-port probe](../../quests/probe-closed-port.md) is extra TCP diagnostic practice, not the raw HTTP lab and not a replacement for a core objective. A refused connection has no HTTP status; a proxy's `502` is an HTTP response.

## Docs Pointers

- Read [Sockets](../../concepts/sockets.md) to connect a host address and port to a service endpoint.
- Read [nc](../../commands/nc.md), [HTTP Inspection](../../concepts/http-inspection.md), and [Reverse Proxy](../../concepts/reverse-proxy.md).
- Read [Platform Reference](../../guides/platform-reference.md) for URL templates.
- Run `man curl`, then search for `-I`, `-L`, and `-v`.
- Run `man diff` for comparison results and `man nc` for local netcat options.
- Read the [MDN HTTP status reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status).

## Next Session

S8: 2026-09-26, your own web service. Run your own backend and manage its lifecycle: start, stop, restart, inspect logs, and keep it alive after logout. Keep your static pages and unchanged `site-check.sh` working.
