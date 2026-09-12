# Check your personal pages

Quest: check-personal-pages

## Mission

Finish `~/scripts/site-check.sh PAGE [PAGE ...]` to accept any page paths, print whether each returned HTTP 200, explain how to rebuild a missing report page, and handle connection failures while continuing to the remaining pages. `""` selects the homepage; no arguments must print usage and exit nonzero (the reference uses `2`). Build on your existing work; create the file only if it is missing.

## Commands You Will Use

The lesson uses these commands to teach the checker. They are not a required source layout; equivalent implementations are accepted.

- `for`
- `if`
- `curl -I`
- `printf`
- `bash`
- `micro`

## Steps

1. Inspect your existing `~/scripts/site-check.sh`. The complete [S6 self-study script](../sessions/S06/self-study.md#complete-script) is one implementation, not a required copy. Finish any missing behavior. If it only checks one argument or hardcodes two pages, continue from [Exercise 2](../sessions/S06/self-study.md#exercise-2-capture-one-answer) through Exercise 5. If it does not exist, start from Exercise 1.
2. Run `bash -n ~/scripts/site-check.sh` and repair any syntax error.
3. Without changing the checker, predict its diagnostics for the cases in the [final exercise](../sessions/S06/self-study.md#exercise-6-predict-then-check). Explain why a homepage `404`, a report `404`, and a curl failure produce different advice. Do not delete a real page to create a failure.
4. Run `bash ~/scripts/site-check.sh "" maker-report.html` and read the real result for each URL. Then run `bash ~/scripts/site-check.sh not-a-page.html` with an unused path to exercise a real `404` without editing the checker or deleting files. Also try no arguments: expect usage help, not a homepage request.
5. If the real report is missing, run `~/scripts/maker-report.sh "S5 Report"`, then `build-website`. If the generator was moved, first follow [S6 preflight recovery](../sessions/S06/self-study.md#preflight); do not replace an existing script.
6. Run the checker again, confirm that both pages return HTTP 200, and open both pages in your laptop browser.
7. Run `guide now` or `guide check` in the classroom shell. For this assigned quest, it automatically runs the simulated cases locally as your learner account with varying page arguments. Follow the fixed case feedback, edit, and retry until all pass.

The [cases](../sessions/S06/self-study.md#guide-checks) cover both pages returning `200`, report `404` with repair advice, homepage or arbitrary-page `404` without report-regeneration advice, report `500`, each page's connection failure while still checking the other, curl printing `200` but exiting nonzero, and no-argument usage help. Controlled fixtures exercise connection failures safely; a real `404` is a response, not a connection failure. A simulated pass does not prove either live page works. Keep the manual script and browser checks above; the reference script's exit code is not an aggregate health result.

Output must identify each page by its URL, path, or a homepage/report label, include the HTTP code and diagnosis or a transport-failure diagnosis, and never claim a failed request succeeded. Report-404 advice must name `maker-report.sh`, then `build-website`. Exact sentences, variable names, `if` nesting, functions versus `case`, page order, and curl flag order are not prescribed.

IRC cannot run the local suite and directs you to the classroom shell. Do not use sudo. An older CLI without local-check support cannot complete this quest by accepting the source instead; ask a mentor to update it.

## Hints

These hints build the lesson's `for`/`if` example; use them to understand the decisions, not to satisfy a source-pattern check.

1. `for page in "$@"` extends the early `page="$1"` exercise to every supplied argument. Before the loop, use `[[ "$#" -eq 0 ]]` to print usage and exit `2` when none are supplied. One empty argument is still a page selection.
2. Set `base_url="https://lf2607.kolamayermakers.org/~$USER"`, then `url="$base_url/$page"` inside the loop.
3. Reset `curl_exit_code=0` for each page. Capture HTTP with `status=$(curl ...)`, followed by `|| curl_exit_code=$?` to record failure. Then `if [[ "$curl_exit_code" -eq 0 ]]` separates a completed request from a connection failure.
4. Inside that branch, `if [[ "$status" == "200" ]]` selects success. A completed curl command does not by itself mean HTTP 200.
5. Check both `"$page" == "maker-report.html"` and `"$status" == "404"` before printing the report repair with `maker-report.sh` and `build-website`.
6. Preserve other HTTP statuses with a curl inspection hint. For connection failures, print a DNS/connection/TLS hint. Close both `if` blocks with `fi` and the loop with `done`.

## If Check Fails

Read the failed case and fixed advice. Check that only supplied page paths are requested, no arguments produce usage help and a nonzero exit, each diagnosis identifies the page, HTTP failures include their codes, and curl failures cannot print success or skip remaining pages. For report `404`, name both repair commands; do not suggest report regeneration for any other page. Use `bash -n` for syntax errors. If the script changed during checking, rerun `guide now` or `guide check`. You do not need to replace working code with the reference example.

## Related Reading

- [S6 self-study](../sessions/S06/self-study.md)
- [curl -I](../commands/curl-head.md)
- [HTTP](../concepts/http.md)
- [IP Networking](../concepts/ip-networking.md)
