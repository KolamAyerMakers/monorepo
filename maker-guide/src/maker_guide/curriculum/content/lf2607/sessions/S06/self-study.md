# S6 Self-Study: Is Your Site Actually Working?

Session: S6

## Study Path

1. Warm up with ping to an IP address and a short traceroute demonstration.
2. Follow the web-request path: look up the classroom hostname with DNS.
3. Inspect headers, page bodies, missing paths, and redirects with curl.
4. Write a one-page checker, capture the status, and choose a message with `if`.
5. Repeat the check for the homepage and report with `for`.
6. Add report repair advice and handle failed connections explicitly.
7. Predict diagnostic messages, run the unchanged checker, then verify both pages from your browser.

## Preflight

Open your classroom SSH session:

```bash
whoami
hostname
guide now
```

In the URLs below, `$USER` expands to your classroom username.

Run `guide now` before a scored activity and again after the work. Command objectives can advance automatically. If the task you just completed remains current, run `guide check`, then `guide now`; if the next task is already current, continue without checking unfinished work. Use `guide answer 'your own observation'` when prompted. Reading an answer does not record progress.

## Provided Report Script

Your S5 version stays in `~/src`. A ready-to-use reference is available on the classroom server at `/docs/guides/resources/maker-report.sh`:

```bash
mkdir -p ~/scripts
cp -i /docs/guides/resources/maker-report.sh ~/scripts/
chmod u+x ~/scripts/maker-report.sh
```

`cp -i` asks before replacing an existing script. Answer `n` to keep your own working version. The copy does not modify your repository or require completed Git homework. If the shared reference is missing, ask the instructor.

Running the script regenerates `~/src/pages/maker-report.md`; `build-website` publishes it. Keep the existing site project and its `pages` directory.

## Network Warm-Up

Use the public IP (Internet Protocol) address `1.1.1.1`, not a hostname:

```bash
ping -c 3 1.1.1.1
```

ICMP (Internet Control Message Protocol) carries network diagnostics and error messages. Ping uses echo requests and replies to measure round-trip time. `-c 3` sends three requests; read packet loss and `min/avg/max` times in milliseconds. Report the actual result, including no replies. `Ctrl-C` cancels.

For the short traceroute demonstration, use the same address:

```bash
traceroute -m 8 1.1.1.1
```

The classroom provides GNU inetutils traceroute. Its UDP probes travel progressively farther; replies reveal some hops. Eight hops may not reach the destination. A `*` means a missing probe reply, not proof of a broken route. `Ctrl-C` cancels.

These are network diagnostics, not steps required to fetch a web page. The destination is not the classroom server; filtering, routing, or destination policy can prevent replies while HTTPS still works.

## From Name To Page

```text
web address -> resolve a name -> connect to a service -> request a path -> response
```

- DNS (Domain Name System) provides records for a name, including IPv4 (`A`) and IPv6 (`AAAA`) addresses.
- HTTP (Hypertext Transfer Protocol) carries web requests and responses. HTTPS is its secure form: TLS (Transport Layer Security) encrypts the exchange and lets the client verify the server certificate. A port identifies the service endpoint; HTTPS normally uses port `443`.

Browsers, SSH clients, and many other programs resolve hostnames before connecting. Cached answers and local name overrides can avoid a DNS lookup on each request. A successful lookup does not prove the service or requested page works.

## DNS Lookup

```bash
host lf2607.kolamayermakers.org
```

Read one complete address answer from `host`, for example `name has address ...` or `name has IPv6 address ...`. The actual addresses may change; use your output, not a copied value.

## HTTP Experiments

`curl -I` sends `HEAD`, asking for response headers without the page body:

```bash
curl -I "https://lf2607.kolamayermakers.org/~$USER/"
curl -I "https://lf2607.kolamayermakers.org/~$USER/maker-report.html"
```

Find a status line such as `HTTP/2 200` or `HTTP/1.1 200 OK`, then `content-type`. Versions and optional headers vary. The homepage and report are independent paths: one can work while the other is missing.

Read status families before memorizing individual numbers:

| Family | Meaning | Common examples |
|---|---|---|
| `2xx` | Success | `200 OK` |
| `3xx` | Redirection or further action | `301`, `302`, `308` redirect; `304` use a cached copy |
| `4xx` | The server cannot fulfil this request | `403` access refused; `404` missing path |
| `5xx` | Server failure | `500` internal error; `502` unusable upstream response |

Fetch the actual report body, then headers and body together:

```bash
curl "https://lf2607.kolamayermakers.org/~$USER/maker-report.html"
curl -i "https://lf2607.kolamayermakers.org/~$USER/maker-report.html"
```

These send `GET`. Find your report title in the HTML. A browser renders that content; curl prints it. Lowercase `-i` includes headers with the body; uppercase `-I` asks for headers only.

Choose a filename you never published:

```bash
curl -I "https://lf2607.kolamayermakers.org/~$USER/not-a-page.html"
```

Expected: `404`. If the file exists, pick another nonexistent filename. Remove `-I` and inspect the error body too. Do not delete an actual page to create this result.

Inspect the classroom's HTTP-to-HTTPS redirect:

```bash
curl -I "http://lf2607.kolamayermakers.org/~$USER/"
curl -I -L "http://lf2607.kolamayermakers.org/~$USER/"
```

Caddy normally returns `308` with a `Location` header. `-L` follows it, showing another response. Our final checker deliberately does not follow redirects: it requires the exact HTTPS paths to return `200`.

## Know The Viewpoint

On the classroom server, `/etc/hosts` maps its public hostname to `127.0.0.1`, the same machine. `host` asks DNS for public records, while curl's normal name resolution can use that local mapping. These two results need not show the same address.

The script proves those page requests work from the server, not that outside clients can reach it. Open both page URLs in your laptop browser as well. Replace `your-handle` in the [homepage URL](https://lf2607.kolamayermakers.org/~your-handle/) and [report URL](https://lf2607.kolamayermakers.org/~your-handle/maker-report.html). Even that is evidence from one outside network, not every visitor's network.

## Exercise 1: One Page

If you already started `~/scripts/site-check.sh` during the session, compare it with the [complete script](#complete-script) and finish any missing stages below. Keep your existing work rather than starting over. Only continue directly to [the final exercise](#exercise-6-predict-then-check) if your script already loops over both pages without arguments and handles HTTP results and connection failures.

If your script is the one-page version below, continue from [Exercise 2](#exercise-2-capture-one-answer) through Exercise 5. Passing `bash -n` checks syntax, not whether the script is complete or runs successfully.

```bash
mkdir -p ~/scripts
cd ~/scripts
micro site-check.sh
```

Type this inside Micro:

```bash
#!/bin/bash
set -euo pipefail

base_url="https://lf2607.kolamayermakers.org/~$USER"
page="$1"
url="$base_url/$page"
curl -I "$url"
```

Save with `Ctrl-S`, quit with `Ctrl-Q`, inspect with `cat site-check.sh`, and run `bash site-check.sh maker-report.html`. This works without execute permission. Keep the shebang for future direct execution.

`page="$1"` uses the first argument, as in S5. With `set -u`, omitting it stops the script with an unset-variable error. Pass `""` to check the homepage: `bash site-check.sh ""`.

Keep `set -euo pipefail` from S5: `-e` stops on an unhandled command failure, `-u` rejects unset variables, and `pipefail` makes a pipeline fail if any command in it fails. A curl connection failure stops this first version; later we will handle it with `if`.

## Exercise 2: Capture One Answer

Replace the last line with:

```bash
status=$(curl -sS -I --max-time 10 -o /dev/null -w '%{http_code}' "$url")
printf 'status=<%s>\n' "$status"
```

- `-sS` removes the progress meter but keeps diagnostic errors.
- `-I` requests headers only.
- `--max-time 10` bounds each request to ten seconds.
- `-o /dev/null` discards the headers, not the diagnostic stream.
- `-w '%{http_code}'` writes the HTTP code to stdout.
- `$()` captures stdout in the variable. Stderr still reaches your terminal.

Run the curl command alone first if the combination is unclear. Add `\n` inside its write-out format when displaying it directly at the prompt. Assignment has no spaces around `=`.

## Exercise 3: Choose A Message

Replace the status-printing line with:

```bash
if [[ "$status" == "200" ]]; then
  printf 'OK: %s returned HTTP 200\n' "$url"
else
  printf 'CHECK: %s returned HTTP %s\n' "$url" "$status"
fi
```

`==` compares text. `[[ ... ]]` is a Bash test, with spaces inside the brackets. `then` runs when the test succeeds; `else` runs otherwise; `fi` ends it. Keep quoting variable expansions consistently, even though `[[ ... ]]` itself prevents word splitting.

Use the page argument to test both branches without editing the script or changing any web files:

```bash
bash ~/scripts/site-check.sh maker-report.html
bash ~/scripts/site-check.sh not-a-page.html
```

Predict each result: `200` selects `OK`; a real `404` selects `CHECK`. Use another unused path if `not-a-page.html` already exists; do not delete a working page.

## Exercise 4: Two Pages

Keep `base_url=...` above the loop. Remove `page="$1"`; the loop will set `page` instead. Replace the single-page body with a list traversal:

```bash
for page in "" maker-report.html; do
  url="$base_url/$page"
  printf 'Checking %s\n' "$url"
done
```

The empty string is still one item: the first URL ends in `/`. The second iteration appends `maker-report.html`. Run it before proceeding and verify that the URLs differ.

Replace the loop's `printf` with your existing curl capture and `if` block. Now the same decision handles each path. Indent the body so the nesting is visible; Bash uses `do`/`done` and `then`/`fi`, not indentation, to determine structure.

Before the existing `else`, insert a report-specific branch:

```bash
elif [[ "$page" == "maker-report.html" && "$status" == "404" ]]; then
  printf 'MISSING: maker-report.html returned HTTP 404\n'
  printf 'Run ~/scripts/maker-report.sh "S5 Report", then build-website.\n'
```

`elif` means "otherwise, test this". Inside `[[ ... ]]`, `&&` requires both tests to succeed. A generic `404` must not pretend every missing path is the report.

Add `printf 'Inspect headers with: curl -I %s\n' "$url"` inside the final `else`, after printing its status.

## Exercise 5: Command Failure Is Different

At the prompt, compare the HTTP status with curl's exit code:

```bash
curl -I "https://lf2607.kolamayermakers.org/~$USER/not-a-page.html"
printf 'curl exit code: %s\n' "$?"
```

Read `$?` immediately: another command replaces it. Receiving `404` normally still means curl exits `0`; a response arrived. DNS, TLS, connection, and timeout failures return a nonzero exit code. With `-w '%{http_code}'`, curl prints `000` when no HTTP response code was received. This placeholder is neither an HTTP status nor curl's exit code; read `$?` for the exit code.

Keep the two results in separate variables. Replace the curl capture inside the loop with:

```bash
curl_exit_code=0
status=$(curl -sS -I --max-time 10 -o /dev/null -w '%{http_code}' "$url") \
  || curl_exit_code=$?
if [[ "$curl_exit_code" -eq 0 ]]; then
```

Reset `curl_exit_code=0` on every iteration. `$()` captures the HTTP status in `status`; the assignment takes curl's exit code. `||` runs its right-hand command only on failure, saving `$?` immediately and preventing `set -e` from stopping the script. The backslash continues the command onto the next line. `-eq` compares numbers.

Place your existing HTTP `if` inside this outer `then`, then add an outer `else` for connection diagnostics and a second `fi` before `done`.

Do not add `-f`: it would turn `404` into a command failure before our explicit HTTP decision. Do not add `-k` to bypass certificates. `set -e` is not a substitute for handling expected failures.

## Complete Script

````bash
#!/bin/bash
set -euo pipefail

base_url="https://lf2607.kolamayermakers.org/~$USER"

for page in "" maker-report.html; do
  url="$base_url/$page"
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
done
````

Save, check, and run:

```bash
bash -n ~/scripts/site-check.sh
bash ~/scripts/site-check.sh
```

`bash -n` parses without executing and normally prints nothing on success. For unexpected behaviour, use `bash -x ~/scripts/site-check.sh`. Add `chmod u+x ~/scripts/site-check.sh` only if you want direct execution instead of `bash`.

This is a human-readable checker, not a complete monitoring system. It prints each result; its process exit code does not summarize website health. A `HEAD` response of `200` does not prove the report's contents are correct or fresh. Inspect the page body and browser view too. Some other servers handle `HEAD` differently from `GET`.

## Exercise 6: Predict, Then Check

Read the unchanged checker and predict its message and advice for these hypothetical results:

| Page | Curl exit code | HTTP status |
|---|---|---|
| Either | `0` | `200` |
| Homepage | `0` | `404` |
| Report | `0` | `404` |
| Either | `0` | `302` or `500` |
| Either | `6` | No response |

Explain why the two `404` cases produce different advice and why a curl failure skips the HTTP decision. Do not change the script or delete a page to produce these cases.

Run `bash ~/scripts/site-check.sh` against your real pages. Read the actual results, repair only observed problems, and rerun. Verify both pages in your laptop browser too.

To observe a failed request without altering your site or checker, try at the prompt:

```bash
if curl -I --max-time 3 https://s6-network-test.invalid; then
  printf 'A response arrived. Read its status.\n'
else
  printf 'The request failed. Read the curl error.\n'
fi
```

`.invalid` is reserved for names that should not resolve. A configured proxy may instead return a response; explain what you actually see. Do not disable TLS checks, alter DNS, or open firewall rules yourself.

## Repair A Missing Report

If the real script prints the report `MISSING` line, use your working generator or the [provided report script](#provided-report-script), then run:

```bash
~/scripts/maker-report.sh "S5 Report"
build-website
bash ~/scripts/site-check.sh
```

Generation writes Markdown; rebuilding publishes HTML. Verify `200`, then open the report in your browser. For a missing homepage, inspect `~/src/pages/index.md` and rebuild; do not overwrite that source file with the report.

## Troubleshooting

| Symptom | Check | Repair |
|---|---|---|
| `command not found` for host, ping, curl, or traceroute | Read the command name | Ask the instructor to verify deployment; do not use sudo or install packages yourself. |
| Wrong username in URLs | Compare `whoami` with `printf '%s\n' "$USER"` | Reconnect with your course account. |
| No DNS address answer | Read the exact host error | Ask the instructor about the resolver or hostname. |
| No ping replies, HTTP works | Read packet loss | Report no replies, not an invented time or "website down". |
| `CONNECTION FAILED` | Read curl's stderr | Distinguish name resolution, refusal, timeout, and TLS failure. Ask for help rather than using `-k`. |
| Homepage `404` | Inspect `~/src/pages/index.md` | Rebuild; ask for recovery if source is missing. |
| Generator path is missing | Inspect `~/scripts/maker-report.sh` | Copy the provided report script; leave your version in `~/src` untouched. |
| Report `404` | Inspect `~/src/pages/maker-report.md` | Generate the report, then rebuild. |
| `301`, `302`, or `308` | Inspect `Location` with curl | Use the documented HTTPS URL and trailing homepage slash. |
| `403`, `500`, or `502` | Preserve the response and URL | Ask the instructor; do not change shared-service permissions or configuration. |
| `syntax error` | Run `bash -n` | Check both `if`/`fi` pairs, `do`/`done`, quotes, and bracket spaces. |
| Both iterations show the same URL | Inspect the loop body | Use `url="$base_url/$page"`, not a fixed homepage URL. |
| Guide accepts source but a page fails | Read the actual output | Guide checks source shape, not public reachability. Repair and retest manually. |

## Proof Checklist

- Explain the different questions answered by DNS, ping, and HTTP.
- Identify an observed status and response header, then find your report title in a `GET` body.
- Explain why curl can exit `0` after an HTTP `404`.
- The checker uses `$USER`, two page paths, `for`, status capture, and conditional diagnostics.
- Predict the diagnostics for missing-report, other HTTP statuses, and curl failures without changing the checker.
- Both real paths return `200` from the server and open correctly in your laptop browser.
- Run `guide check`. This records source/command evidence, not independent execution of your script or proof of live HTTP success.

## Next Session

You have already inspected HTTP statuses, headers, and bodies. In S7, compare generated HTML with fetched HTML, add and link another page, and inspect a raw HTTP exchange and the separate personal service route. Keep your report and checker working.

## Optional Practice

Compare a known-list `for` with a condition-controlled `while` at the prompt:

```bash
remaining=3
while [[ "$remaining" -gt 0 ]]; do
  printf '%s\n' "$remaining"
  remaining=$((remaining - 1))
done
```

`-gt` means numerically greater than; `$((...))` performs arithmetic. The update makes the loop stop. This is optional, not a guide gate.

Optional Git practice: inspect `~/src/scripts/site-check.sh` before copying your working script there; do not overwrite an existing version without comparing it. Use S4's deliberate stage, diff, commit workflow. Git completion is not a prerequisite or live objective here.

## Docs Pointers

- Run `man host`, `man ping`, `man curl`, and `man traceroute`.
- Read [DNS](../../concepts/dns.md), [ICMP](../../concepts/icmp.md), [HTTP](../../concepts/http.md), and [HTTP Status Codes](../../concepts/http-status-codes.md).
- Read [IP Networking](../../concepts/ip-networking.md) for diagnostic layers.
- Read [curl](../../commands/curl.md), [curl -I](../../commands/curl-head.md), and [traceroute](../../commands/traceroute.md).
- Run `help if`, `help for`, `help [[`, and optionally `help while`.
- Read [Conditionals](../../concepts/conditionals.md) and [Shell Scripting](../../concepts/shell-scripting.md).
