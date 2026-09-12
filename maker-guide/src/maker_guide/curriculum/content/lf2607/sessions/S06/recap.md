# S6 Recap: Is Your Site Actually Working?

Session: S6

## What You Built

`~/scripts/site-check.sh PAGE [PAGE ...]` constructs URLs from any supplied page paths using `$USER`, checks each response, and prints a diagnosis. It does not regenerate the report or publish files automatically.

## Three Questions

- DNS: what records, such as addresses, exist for this name? Use `host`.
- ICMP (Internet Control Message Protocol): carries network diagnostics and errors. Use `ping` to ask whether echo replies return and how long they take.
- HTTP: what happened when we requested this page? Use `curl`.

DNS success does not prove a page exists. Failed ping does not prove HTTPS is down. The public ping target is not the classroom server.

On the classroom server, curl can use `/etc/hosts` to reach local Caddy. Open the pages in your laptop browser too: the script alone does not test public reachability.

## Read HTTP

- `curl URL`: `GET`, prints the response body.
- `curl -i URL`: `GET`, prints headers and body.
- `curl -I URL`: `HEAD`, prints headers without a body.
- `-L`: follow redirects. The lesson's exact-URL example deliberately does not use it.

| Family | Meaning | Examples |
|---|---|---|
| `2xx` | Success | `200 OK` |
| `3xx` | Redirection or further action | `301`, `302`, `308` redirect; `304` reuse cache |
| `4xx` | Request cannot be fulfilled | `403` forbidden, `404` missing path |
| `5xx` | Server failure | `500` internal error, `502` bad gateway |

With `-w '%{http_code}'`, curl prints `000` when no HTTP response code was received. It is not an HTTP status or an exit code.

## Two Decisions

```text
for each page:
  if curl completes successfully:
    if HTTP status is 200: print OK
    elif report is 404: print the report repair
    else: print the actual status and an inspection hint
  else: report a connection failure and read curl's error
```

`$()` captures the HTTP status in `status`. Start each iteration with `curl_exit_code=0`; `|| curl_exit_code=$?` records a failure. The outer `[[ "$curl_exit_code" -eq 0 ]]` checks curl's exit code; the inner `[[ "$status" == "200" ]]` checks HTTP. A `404` can still give curl exit code `0` because a response arrived.

Keep `set -euo pipefail`. Handling the failed capture with `||` lets the script report the error and continue the loop under `set -e`.

`for page in "$@"` extends the early `page="$1"` exercise to all supplied arguments. `""` selects the homepage; zero arguments print usage and exit `2`. `elif` tries another condition. The report repair requires both the report filename and `404`, using `&&`.

That describes the lesson example, not a required source layout. Equivalent functions, `case` statements, variable names, conditional nesting, page order, and curl flag order are accepted. Identify each page by URL, path, or homepage/report label and print its HTTP code with a diagnosis, or a clear transport-failure diagnosis. Never call a failed request successful, even if curl printed `200` before exiting nonzero.

## Run And Repair

```bash
bash -n ~/scripts/site-check.sh
bash ~/scripts/site-check.sh "" maker-report.html
bash ~/scripts/site-check.sh not-a-page.html
```

Use an unused path for a real `404`, without editing statuses or deleting files. That path must not trigger report-regeneration advice. For a missing report, run `~/scripts/maker-report.sh "S5 Report"`, then `build-website`, then the checker again.

If the generator is missing, use the [provided report script](self-study.md#provided-report-script). Your S5 version in `~/src` stays untouched.

Each request has a ten-second timeout. Keep certificate verification enabled. This script prints human-readable results; its exit code is not an aggregate health result, and `HEAD 200` does not prove the page contents are correct or fresh.

## Live Core

You can explain the three network questions, inspect headers and a body, and explain which branch handles an HTTP response versus a command failure. Both real paths return `200`, and the pages open in your laptop browser.

For the current checker objective or assigned quest, `guide now` or `guide check` in the classroom shell automatically runs your script locally under your own account with varying page arguments. IRC directs you back to that shell. The [simulated cases](self-study.md#guide-checks) cover both `200`, report `404` with `maker-report.sh` then `build-website` advice, homepage or arbitrary-page `404` without report-regeneration advice, report `500`, each page's connection failure while still checking the other, a printed `200` with a nonzero curl exit, and no-argument usage help. Controlled fixtures test connection failures safely; a real `404` is an HTTP response, not a connection failure.

Follow the fixed case feedback and rerun after edits. A pass verifies simulated behavior, not live health: still run `bash ~/scripts/site-check.sh "" maker-report.html` and inspect both pages in your browser. An unavailable or older CLI needs mentor help, not a reference-source workaround.

## Next Session

You already know HTTP statuses, headers, and bodies. In S7, compare generated and fetched HTML, add and link a page, and inspect a raw HTTP exchange and the separate personal service route.

## Reinforcement

Run `guide now` for DNS, ping, header, and checker quests. Submit your own requested observations with `guide answer 'your answer'`, then `guide check`. No ping reply is valid evidence; do not invent latency.

Optional: repeat the traceroute warm-up to explore hops, or try `while` to repeat while a condition succeeds. Neither adds a scored goal. Git homework is independent of S6 completion.

## Full Autonomy

Use the [self-study guide](self-study.md) for every stage, the full checker, diagnostic predictions, and recovery steps.
