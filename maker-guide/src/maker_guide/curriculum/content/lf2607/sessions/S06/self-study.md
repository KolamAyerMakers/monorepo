# S6 — Is Your Site Actually Working?

Inspect a web response, then write a checker that repeats a request and explains the result.

**You need:** `curl`, `host`, `ping`, `traceroute`, and your homepage and S5 report. In class, use your SSH shell. At home, follow [Continue at Home](../../guides/continue-at-home.md) and keep the local preview running in another terminal.

## Preflight

If your report generator is missing, inspect the supplied version before copying it:

```bash
mkdir -p ~/scripts
cp -i /docs/guides/resources/maker-report.sh ~/scripts/
chmod u+x ~/scripts/maker-report.sh
```

At home, the same reference is in `~/linux-foundations-practice/answers/maker-report.sh`. Answer `n` to keep an existing working script. Run it with a quoted title, then rebuild your site.

## 1. Separate the network questions

```text
name → address → connection → HTTP request → response
```

- **DNS** gives records for names, including IPv4 (`A`) and IPv6 (`AAAA`) addresses.
- A **port** identifies a service endpoint. HTTPS usually uses `443`.
- **HTTP** carries requests and responses. **HTTPS** protects that exchange with TLS encryption and server identity verification.

```bash
host lf2607.kolamayermakers.org
ping -c 3 1.1.1.1
traceroute -m 8 1.1.1.1
```

If the course hostname has retired, use `example.com` for the DNS lookup.

Read an address answer, ping's packet loss and round-trip times, and traceroute's hops. Ping uses ICMP; this traceroute uses UDP probes. A `*` means no probe reply, not proof that the route is broken. Eight hops may not reach the destination.

These probes target a public diagnostic address, not your website. No ping reply does not prove HTTPS is down; filtering may treat them differently.

## 2. Inspect headers and content

Choose the base address for **this shell**:

```bash
BASE_URL="https://lf2607.kolamayermakers.org/~$USER"
```

**At home, use `BASE_URL="http://localhost:8080"` instead.** No trailing slash: the commands add it.

```bash
curl -I "$BASE_URL/"
curl -I "$BASE_URL/maker-report.html"
curl "$BASE_URL/maker-report.html"
curl -i "$BASE_URL/maker-report.html"
```

`-I` sends `HEAD`: headers, no body. Lowercase `-i` includes headers with the normal `GET` body. Find the status, `content-type`, and your report title in the HTML.

| Family | Meaning | Examples |
|---|---|---|
| `2xx` | Success | `200` |
| `3xx` | Redirection or further action | `301`, `302`, `308`; `304` means use cached content |
| `4xx` | Request cannot be fulfilled | `403` access refused; `404` missing path |
| `5xx` | Server failure | `500`; `502` unusable upstream response |

Request an unpublished filename:

```bash
curl -I "$BASE_URL/not-a-page.html"
printf 'curl exit code: %s\n' "$?"
```

Expect `404` if that path is absent, usually with curl exit code **`0`**: a response arrived. Read `$?` immediately; the next command replaces it. DNS, TLS, connection, and timeout failures instead give nonzero exit codes.

**Classroom extension:** compare `curl -I "http://lf2607.kolamayermakers.org/~$USER/"` with the same command plus `-L`. Shared Caddy normally redirects HTTP to HTTPS with `308`; `-L` follows `Location`.

## 3. Capture one answer

Create `~/scripts/site-check.sh` with Micro. Preserve existing work if you already started it.

```bash
#!/bin/bash

base_url="${BASE_URL:-https://lf2607.kolamayermakers.org/~$USER}"
page="$1"
url="$base_url/$page"
status=$(curl -sS -I --max-time 10 -o /dev/null -w '%{http_code}' "$url")
printf 'status=<%s>\n' "$status"
```

`$()` captures stdout. Here curl discards headers with `-o /dev/null`, then writes only the response code using `-w`. `-sS` removes the progress meter but keeps errors; `--max-time 10` bounds the request.

The default is the class site. At home, pass the override into the script's environment:

```bash
export BASE_URL="http://localhost:8080"
bash ~/scripts/site-check.sh maker-report.html
```

An unexported shell variable is not inherited by a child script. In class, the default works without an override.

## 4. Choose a message, then repeat

Replace the status-printing line with:

```bash
if [[ "$status" == "200" ]]; then
  printf 'OK: %s returned HTTP 200\n' "$url"
else
  printf 'CHECK: %s returned HTTP %s\n' "$url" "$status"
fi
```

`[[ ... ]]` is a Bash test; `==` compares text. `then` and `else` choose branches; `fi` closes the decision.

Try a real page and an absent path. Next, remove `page="$1"` and put the URL, curl capture, and decision inside:

```bash
for page in "$@"; do
  # Put the per-page commands here.
done
```

`"$@"` preserves each argument. `""` is one empty argument, selecting the homepage; no arguments should show usage instead. `$#` counts arguments; `-eq` compares numbers.

## 5. Handle failure separately

HTTP status and curl exit code answer different questions. Curl's `000` means no HTTP response code was received; it is not an HTTP status or curl's exit code.

Use this complete example to compare with your script. The outer `if` tests whether curl succeeded; the inner one interprets HTTP. A failed request must not claim success, even if curl printed `200` before failing.

````bash
#!/bin/bash
set -euo pipefail

if [[ "$#" -eq 0 ]]; then
  printf 'Usage: site-check.sh PAGE [PAGE ...] (use "" for homepage)\n' >&2
  exit 2
fi

base_url="${BASE_URL:-https://lf2607.kolamayermakers.org/~$USER}"

for page in "$@"; do
  url="$base_url/$page"
  curl_exit_code=0
  status=$(curl -sS -I --max-time 10 -o /dev/null -w '%{http_code}' "$url") || curl_exit_code=$?
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
done
````

New syntax:

- `||` runs its right side only after failure; capture `$?` immediately. Reset the saved exit code for each page.
- `elif` adds a test; `&&` inside `[[ ... ]]` requires both conditions.
- `set -u` rejects unset variables. `pipefail` propagates pipeline failures. `set -e` exits on certain unhandled failures, but has exceptions; the explicit `||` handles this expected curl failure.
- `${BASE_URL:-...}` uses the override if nonempty, otherwise the default.

At home, change the report-repair message to suggest `cd ~/src && node scripts/build.mjs` instead of `build-website`. Do not add `-k` to bypass certificates or `-f` to turn HTTP errors into curl failures in this checker.

```bash
bash -n ~/scripts/site-check.sh
bash ~/scripts/site-check.sh "" maker-report.html
```

This prints results for people; its exit code does **not** summarize site health. `HEAD 200` does not prove correct or fresh content. Check the body and browser too.

## Diagnostic Cases

Predict the message and advice without deleting pages or editing the checker:

| Page | Curl exit | HTTP code | What should it diagnose? |
|---|---|---|---|
| Either | `0` | `200` | Successful response |
| Report | `0` | `404` | Missing report; generation, then build |
| Another path | `0` | `404` | Missing path; not report regeneration |
| Either | `0` | `302` or `500` | Actual HTTP code; inspect headers |
| Either | `6` | `000` | Failed request; continue to next argument |
| Report | `28` | `200` | Failed request, not success |

Run the checker with an absent path and with no arguments. The latter should print usage and exit `2`. Then check both real pages.

At home, stop the local preview with `Ctrl-C` in its terminal and check both paths again. Expect connection-failure diagnoses for both, not HTTP statuses. Restart the same preview command and confirm recovery; no website files need changing.

**Classroom viewpoint:** curl may resolve the course hostname through `/etc/hosts` to loopback, while `host` queries public DNS. Server-side success is not proof of outside access. Open both public pages in your laptop browser as well.

## Check yourself

- Explain the different questions answered by DNS, ping, curl's exit code, and HTTP status.
- Explain why `""` and zero arguments are different.
- Explain how `for`, `"$@"`, and `if` check arbitrary supplied paths.
- Find your report title in a `GET` response and browser view.

[Answers](../../guides/self-study-answers.md#s6-site-checker). References: [curl](../../commands/curl.md), [Conditionals](../../concepts/conditionals.md), and [DNS](../../concepts/dns.md).

## If you get stuck

- Syntax error: `bash -n` checks quotes, bracket spaces, `if`/`fi`, and `do`/`done`.
- Repeated wrong URL: calculate `url` inside the loop, using `page`.
- Report `404`: regenerate Markdown, then build; restarting a server cannot create it.
- Connection failure: read curl's error before changing anything. At home, confirm the preview is running; in class, bring the URL and exact error to support.
