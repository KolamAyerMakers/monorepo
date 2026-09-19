# Linux Foundations S6

Session: S6

Is Your Site Actually Working?

Today you will:

- follow a web request;
- investigate your own site;
- write a checker that makes decisions.

<!-- end_slide -->

# Network Warm-Up: Ping

ICMP (Internet Control Message Protocol) carries diagnostics. Ping asks for echo replies.

```bash
ping -c 3 1.1.1.1
```

- `-c 3`: three requests to a public address.
- Read packet loss and average time in milliseconds.

<!-- end_slide -->

# Quick Demo: Traceroute

Send probes one hop farther each time:

```bash
traceroute -m 8 1.1.1.1
```

`-m 8`: up to eight hops toward this public address.

`*`: no reply, not proof of a broken route. `Ctrl-C` cancels.

<!-- end_slide -->

# Start On The Classroom Server

Open your classroom SSH session. For S6, take the provided report script:

```bash
mkdir -p ~/scripts
cp -i /docs/guides/resources/maker-report.sh ~/scripts/
chmod u+x ~/scripts/maker-report.sh
```

Your committed version stays in `~/src`. `cp -i` asks before overwriting.

<!-- end_slide -->

# What Happens When You Open A Page?

```text
web address -> find an IP address -> connect -> request a page -> response
```

- IP (Internet Protocol) address: where to connect.
- Port: which service.

Which step could fail?

<!-- end_slide -->

# DNS: Find The Address

DNS (Domain Name System): look up a name's addresses.

```text
$ host lf2607.kolamayermakers.org
lf2607.kolamayermakers.org has address 213.163.207.98
lf2607.kolamayermakers.org has IPv6 address 2a04:3543:1000:2310:2cdf:9ff:fe55:6e95
```

<!-- end_slide -->

# HTTP: Ask For A Page

HTTP (Hypertext Transfer Protocol): a request and a response.

```text
request:   GET /~learner/maker-report.html
response:  status 200, content-type text/html, HTML body
```

HTTPS adds TLS (Transport Layer Security): encryption and server verification.

The browser renders HTML. Curl shows the response.

<!-- end_slide -->

# HTTP Status Codes

| Family | Meaning | Examples |
|---|---|---|
| `2xx` | Success | `200 OK` |
| `3xx` | Redirection or further action | `301`, `302`, `308`: read `Location` |
| `4xx` | Request cannot be fulfilled | `403` forbidden; `404` not found |
| `5xx` | Server failure | `500` internal error; `502` bad gateway |

<!-- end_slide -->

# Look At Headers First

`-I` sends `HEAD`: headers, no body.

Example headers (excerpt):

```text
$ curl -I "https://lf2607.kolamayermakers.org/~$USER/"
HTTP/2 200
content-type: text/html; charset=utf-8
server: Caddy
content-length: 5019

$ curl -I "https://lf2607.kolamayermakers.org/~$USER/maker-report.html"
HTTP/2 200
content-type: text/html; charset=utf-8
server: Caddy
content-length: 2683
```

Both return `200`. `content-length` describes the body size in bytes.

<!-- end_slide -->

# Get The Actual Page

Without `-I`: `GET` the body.

```text
$ curl "https://lf2607.kolamayermakers.org/~$USER/maker-report.html"
```

Example body (excerpt):

```html
<h1 id="foo-bar">foo bar</h1>
...
<li>Hostname: lf2607</li>
...
<h2 id="shell-fields-in-etcpasswd">Shell fields in /etc/passwd</h2>
```

Find your report title in the HTML.

Try `-i`: headers **and** body. Different from `-I`.

<!-- end_slide -->

# Make A Safe 404

Request an unpublished path, without deleting any files:

```text
$ curl -I "https://lf2607.kolamayermakers.org/~$USER/not-a-page.html"
HTTP/2 404
server: Caddy
```

Response excerpt: the server replied, but the path is missing.

Remove `-I`. Does the error have a body?

<!-- end_slide -->

# Follow A Redirect

`-L` follows the URL in `Location`.

```text
$ curl -I "http://lf2607.kolamayermakers.org/~$USER/"
HTTP/1.1 308 Permanent Redirect
Location: https://lf2607.kolamayermakers.org/~$USER/

$ curl -L -I "http://lf2607.kolamayermakers.org/~$USER/"
HTTP/1.1 308 Permanent Redirect
Location: https://lf2607.kolamayermakers.org/~$USER/

HTTP/2 200
content-type: text/html; charset=utf-8
```

Example excerpts use `$USER` in place of the returned username.

Our lesson example checks for `200` without following redirects.

<!-- end_slide -->

# Build The Checker

```bash
mkdir -p ~/scripts
cd ~/scripts
micro site-check.sh
```

Start with one page:

```bash
#!/bin/bash
set -euo pipefail

base_url="https://lf2607.kolamayermakers.org/~$USER"
page="$1"
url="$base_url/$page"
curl -I "$url"
```

`$1` is the first argument. Save, then run `bash site-check.sh maker-report.html`.

<!-- end_slide -->

# Ask Curl For Just The Code

Replace `curl -I "$url"` with:

```bash
curl -sS -I --max-time 10 -o /dev/null -w '%{http_code}\n' "$url"
```

- `-sS`: hide progress, keep errors.
- `--max-time 10`: ten-second limit.
- `-o /dev/null`: discard the headers.
- `-w`: print the status code.

<!-- end_slide -->

# Store The Answer

Capture it:

```bash
status=$(curl -sS -I --max-time 10 -o /dev/null -w '%{http_code}' "$url")
printf 'status=<%s>\n' "$status"
```

`$()` captures stdout. Stderr stays visible.

What is stored in `status`?

<!-- end_slide -->

# Let The Script Decide

Replace the status `printf` with:

```bash
if [[ "$status" == "200" ]]; then
  printf 'OK: %s returned HTTP 200\n' "$url"
else
  printf 'CHECK: %s returned HTTP %s\n' "$url" "$status"
fi
```

- `[[ ... ]]` tests a condition; keep spaces inside.
- `==` compares text.
- `then` / `else`: two branches. `fi`: end.

<!-- end_slide -->

# Your Script So Far

Save this in `~/scripts/site-check.sh`:

```bash
#!/bin/bash
set -euo pipefail

base_url="https://lf2607.kolamayermakers.org/~$USER"
page="$1"
url="$base_url/$page"
status=$(curl -sS -I --max-time 10 -o /dev/null -w '%{http_code}' "$url")

if [[ "$status" == "200" ]]; then
  printf 'OK: %s returned HTTP 200\n' "$url"
else
  printf 'CHECK: %s returned HTTP %s\n' "$url" "$status"
fi
```

Run `bash ~/scripts/site-check.sh maker-report.html`.

<!-- end_slide -->

# Exercise: Make Both Branches Run

Same script, different arguments. Predict each result:

```bash
bash ~/scripts/site-check.sh maker-report.html
bash ~/scripts/site-check.sh not-a-page.html
```

`200` selects `OK`; `404` selects `CHECK`. No script edits needed.

Trace the missing-page check with `bash -x ~/scripts/site-check.sh not-a-page.html`.

<!-- end_slide -->

# Check Every Page In One Loop

Extend `$1` (the first argument) to `"$@"` (all arguments). The loop makes `page` from each supplied argument:

```bash
for page in "$@"; do
  url="$base_url/$page"
  printf 'Checking %s\n' "$url"
done
```

Put this in your script below `base_url`, replacing the one-page body. Run `bash ~/scripts/site-check.sh "" maker-report.html`: `""` is a real argument that selects the homepage; any other supplied path is accepted too.

Replace the `printf` with your curl capture and your `if` decision, inside the loop. `page` comes from the loop now, not `$1`.

<!-- end_slide -->

# No Arguments: Print Usage

Add this after `set -euo pipefail`, before building URLs:

```bash
if [[ "$#" -eq 0 ]]; then
  printf 'Usage: site-check.sh PAGE [PAGE ...] (use "" for homepage)\n' >&2
  exit 2
fi
```

`$#` counts arguments. Zero prints help and exits `2`; one empty argument checks the homepage.

<!-- end_slide -->

# The Complete Checker

Keep the usage guard above `base_url`; the body is now:

```bash
base_url="https://lf2607.kolamayermakers.org/~$USER"

for page in "$@"; do
  url="$base_url/$page"
  status=$(curl -sS -I --max-time 10 -o /dev/null -w '%{http_code}' "$url")
  if [[ "$status" == "200" ]]; then
    printf 'OK: %s returned HTTP 200\n' "$url"
  else
    printf 'CHECK: %s returned HTTP %s\n' "$url" "$status"
  fi
done
```

Run `bash ~/scripts/site-check.sh "" maker-report.html`. Reverse the arguments or supply just one page; the loop visits the supplied paths.

<!-- end_slide -->

# Give A Useful Repair Hint

Before the existing `else`, add:

```bash
elif [[ "$page" == "maker-report.html" && "$status" == "404" ]]; then
  printf 'MISSING: maker-report.html returned HTTP 404\n'
  printf 'Run ~/scripts/maker-report.sh "S5 Report", then build-website.\n'
```

`elif`: another test. `&&`: both conditions must be true.

Inside the final `else`, also add:

```bash
printf 'Inspect headers with: curl -I %s\n' "$url"
```

<!-- end_slide -->

# HTTP Status vs Exit Code

HTTP status: the server's response. Exit code: did curl succeed?

```bash
curl -I "https://lf2607.kolamayermakers.org/~$USER/not-a-page.html"
printf 'curl exit code: %s\n' "$?"
```

- HTTP `404`, curl exit code `0`: a response arrived.
- Nonzero exit code: curl failed.

With `-w '%{http_code}'`, curl prints `000` when no HTTP response code was received.
It is not an HTTP status or an exit code.

<!-- end_slide -->

# If Can Test A Command Too

Try a name that should not resolve:

```bash
if curl -I --max-time 3 https://s6-network-test.invalid; then
  printf 'A response arrived. Read its status.\n'
else
  printf 'The request failed. Read the curl error.\n'
fi
```

Exit code `0` selects `then`; nonzero selects `else`. Which branch ran?

<!-- end_slide -->

# Handle A Failed Request

Replace the capture and decision inside the loop:

```bash
curl_exit_code=0
status=$(curl -sS -I --max-time 10 -o /dev/null -w '%{http_code}' "$url") \
  || curl_exit_code=$?
if [[ "$curl_exit_code" -eq 0 ]]; then
  if [[ "$status" == "200" ]]; then
    printf 'OK: %s returned HTTP 200\n' "$url"
  elif [[ "$page" == "maker-report.html" && "$status" == "404" ]]; then
    printf 'MISSING: maker-report.html returned HTTP 404\n'
    printf 'Run ~/scripts/maker-report.sh "S5 Report", then build-website.\n'
  else
    printf 'CHECK: %s returned HTTP %s\n' "$url" "$status"
    printf 'Inspect headers with: curl -I %s\n' "$url"
  fi
else
  printf 'CONNECTION FAILED: %s\n' "$url"
  printf 'Read the curl error: check name, connection, or certificate.\n'
fi
```

`||` captures failure without stopping under `set -e`. `-eq` compares numbers.

<!-- end_slide -->

# Exercise: Predict The Message

Without editing the script, predict the message for each case:

| Page | Curl exit code | HTTP status |
|---|---|---|
| Homepage | `0` | `404` |
| Report | `0` | `404` |
| Either | `0` | `302` or `500` |
| Either | `6` | No response |
| Report | `28` | `200` printed before curl failed |

Then check your real pages:

```bash
bash -n ~/scripts/site-check.sh
bash ~/scripts/site-check.sh "" maker-report.html
bash ~/scripts/site-check.sh not-a-page.html
```

<!-- end_slide -->

# Exit Goal

Explain to your neighbour:

- What do DNS, ping, and HTTP each tell you?
- Why can HTTP `404` give curl exit code `0`?
- What does each `if` decide?
- Can the homepage return `200` while the report returns `404`? Why?

<!-- end_slide -->

# Between-Session Practice

Practice DNS, ping, HTTP headers, and your checker. Compare predictions with actual output and explain any differences to another learner.

Keep `site-check.sh`. Optional: preserve it in Git.

<!-- end_slide -->

# Optional: Repeat While A Condition Holds

`while` repeats while its test succeeds:

```bash
remaining=3
while [[ "$remaining" -gt 0 ]]; do
  printf '%s\n' "$remaining"
  remaining=$((remaining - 1))
done
```

`-gt` compares numbers. `$((...))` calculates a new value.

When does it stop? Without the update, it loops forever. `Ctrl-C` cancels.

<!-- end_slide -->

<a id="next-session-your-page-on-the-wire"></a>

# Next Session: Run Your Own Web Server

S7: 2026-09-19

You can now inspect a web response and explain your checker's decisions. Keep `site-check.sh` and your report working.

- Start your own web server manually behind the personal service route.
- Watch the backend log as requests arrive.
- Match your process PID to its listening port and send raw HTTP.
- Diagnose and recover three safe incidents; publishing remains optional.

For extra help, run `guide` in the classroom terminal.
