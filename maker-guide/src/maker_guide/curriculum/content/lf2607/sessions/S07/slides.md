# Linux Foundations S7

Session: S7

Your page on the wire

S7: 2026-09-19

<!-- end_slide -->

# Today's Story

S6 read HTTP responses and automated two page checks. Today we compare served bytes with your files and investigate the separate service route.

Four goals: inspect headers, compare generated HTML with a fetched body, diagnose the service route, and publish a linked setup page.

<!-- end_slide -->

# Reuse Your Static Preflight

Run on the classroom server in your personal SSH account, not in your laptop's local shell:

```bash
whoami
printf '%s\n' "$USER"
bash ~/scripts/site-check.sh
guide now
```

`$USER` must match `whoami`. Keep the S6 checker unchanged: it checks the homepage and `maker-report.html`, two paths on the same static host. Read both results and repair static failures before continuing.

Checkpoint routine: successful commands can auto-complete command-history objectives. After each task, run `guide now` first. If the task you just finished is still current, run `guide check`, then `guide now`. If the next task is already current, continue without checking that unfinished task.

<!-- end_slide -->

# 1. Inspect Headers Again

```bash
curl -I --max-time 10 "https://lf2607.kolamayermakers.org/~$USER/"
```

As in S6, `-I` sends `HEAD`: response headers, no page body. Identify the actual status and `content-type`. Read `Location` if redirected; do not invent a `200`.

Use the checkpoint routine: `guide now` first.

<!-- end_slide -->

# 2. Compare Three Views

```text
~/src/pages/index.md -> build-website -> ~/public_html/index.html -> HTTP body
```

```bash
build-website
cat ~/src/pages/index.md
cat ~/public_html/index.html
```

Stop if the build fails. Find your heading in both files: Markdown describes the page; generated HTML contains tags and layout. Edit the source, not the generated file.

<!-- end_slide -->

# Fetch The Body And Compare

```bash
mkdir -p ~/playground
curl -fSs --max-time 10 -o ~/playground/s7-index-from-web.html \
  "https://lf2607.kolamayermakers.org/~$USER/"
```

This sends `GET`. `-f` fails on HTTP errors; `-sS` hides progress but keeps errors; `-o` saves only the body. Do not add `-I` or `-i` to the saved comparison.

Only after curl succeeds:

```bash
diff -u ~/public_html/index.html ~/playground/s7-index-from-web.html
```

No output and exit status `0` mean identical files. Status `1` means differences; `2` means an error. These files should match: investigate any mismatch, rebuild, and refetch. Once they match, use the checkpoint routine: `guide now` first.

<!-- end_slide -->

# Send HTTP Without Curl

Use the existing Caddy server's plaintext loopback port. Do not start another server:

```bash
printf 'GET /~%s/ HTTP/1.1\r\nHost: lf2607.kolamayermakers.org\r\nConnection: close\r\n\r\n' "$USER" | nc -w 3 127.0.0.1 80
```

`127.0.0.1` is this classroom machine. If `nc` is missing, ask the instructor.

<!-- end_slide -->

# Read The Request You Built

- `GET /~username/ HTTP/1.1`: method, path, protocol version. `printf` substitutes `$USER` for `%s`.
- `Host`: selects the classroom hostname even though TCP connects to a numeric loopback address.
- `\r\n`: carriage return plus line feed (CRLF), the HTTP/1.1 line ending.
- Final `\r\n\r\n`: ends the last header and sends the blank line that finishes the headers. This request has no body.
- `Connection: close`: asks the server to close after responding.
- `nc -w 3`: limits connection and idle waits to three seconds. `Ctrl-C` cancels.

`nc` carries TCP bytes; it does not construct HTTP for you.

<!-- end_slide -->

# Expect A Redirect, Not Your HTML

Caddy normally returns `HTTP/1.1 308 Permanent Redirect` here, with an HTTPS `Location`. Identify the status and destination in your actual output.

This is the HTTP-to-HTTPS redirect from S6, now exposed as raw bytes. A `3xx` redirect is not the `200` page body you compared. `nc` does not follow it.

Plain `nc` to port `443` cannot speak TLS. Use curl for HTTPS; do not disable certificate checks. If the status differs or nothing returns, report that evidence instead of copying the expected status.

<!-- end_slide -->

# 3. A Different Host, A Different Route

```bash
curl -v --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
```

S6's two URLs were two static paths. This user subdomain is the service URL, sometimes called the "second URL" by the guide. It is not `maker-report.html`.

```text
static host /~username/ -> Caddy -> public_html/index.html
username subdomain /  -> Caddy -> personal backend process
```

Read `*` connection/TLS details, `>` request headers, and `<` response headers. With routing working, expect `502` before S8 because no personal backend is listening yet. DNS or TLS failure happens earlier; it is not an HTTP `502`. Report the actual result and do not start a backend today.

Use the checkpoint routine: `guide now` first.

<!-- end_slide -->

# 4. Create A Useful Setup Page

```bash
micro ~/src/pages/setup.md
```

If it exists, improve it rather than replacing it. Otherwise start with:

```markdown
# My Setup

I edit Markdown in ~/src/pages/ and publish with build-website.

[Back to my homepage](index.html)
```

Add your own useful notes, not passwords, keys, or tokens. Save with `Ctrl-S`, quit with `Ctrl-Q`.

<!-- end_slide -->

# Link, Rebuild, Open

```bash
micro ~/src/pages/index.md
```

Add this without removing existing content or links:

```markdown
[My setup](setup.html)
```

```bash
build-website
cat ~/public_html/setup.html
curl -I --max-time 10 "https://lf2607.kolamayermakers.org/~$USER/setup.html"
```

Open your homepage in your laptop browser and follow the setup link, then the link back. Link to `.html`, not source `.md`. Use the checkpoint routine: `guide now` first. Check the completed setup task only if it remains current.

<!-- end_slide -->

# Exit Goal

- Identify a real status and header.
- Show the generated-file versus fetched-body comparison, and explain why Markdown differs.
- Explain the raw request's blank terminator and HTTPS redirect.
- Distinguish static paths from the service subdomain and explain the missing backend.
- Keep headed `setup.md`, its homepage link, and rebuilt `setup.html`.

The four guide objectives are core work. Guide evidence does not independently prove a successful HTTP response or matching body; inspect your results too.

<!-- end_slide -->

# Between-Session Practice Route

Use the [self-study guide](self-study.md) to finish any missing core work. Then the S7 quests offer optional reinforcement, not a replacement for the four objectives:

- Repeat header inspection and source/output comparisons.
- Publish ASCII art with a fenced code block.
- Try the [closed-port probe](../../quests/probe-closed-port.md) and distinguish TCP refusal from an HTTP response.
- Explain the already-learned `200`, `404`, and `502` using your own observations.

Run `guide now` for your current session objective; after you complete it, it shows your current quest. Submit prompted observations with `guide answer 'your own observation'`, then follow the checkpoint routine.

<!-- end_slide -->

# Next Session: Your Own Web Service

S8: 2026-09-26

Run your own backend behind the service subdomain. Learn its lifecycle: start, stop, restart, inspect logs, and keep it running after logout. Keep your static site and unchanged `site-check.sh` working.
