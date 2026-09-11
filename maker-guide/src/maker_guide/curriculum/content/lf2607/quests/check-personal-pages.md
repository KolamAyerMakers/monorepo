# Check your personal pages

Quest: check-personal-pages

## Mission

Finish `~/scripts/site-check.sh` so one run without arguments checks your homepage and `maker-report.html`, prints whether each page returned HTTP 200, explains how to rebuild a missing report page, and handles connection failures. Build on your existing work; create the file only if it is missing.

## Commands You Will Use

- `for`
- `if`
- `curl -I`
- `printf`
- `bash`
- `micro`

## Steps

1. Inspect your existing `~/scripts/site-check.sh` and compare it with the complete [S6 self-study script](../sessions/S06/self-study.md#complete-script). Finish any missing stages. If it still uses `page="$1"`, continue from [Exercise 2](../sessions/S06/self-study.md#exercise-2-capture-one-answer) through Exercise 5. If it does not exist, start from Exercise 1.
2. Run `bash -n ~/scripts/site-check.sh` and repair any syntax error.
3. Without changing the checker, predict its diagnostics for the cases in the [final exercise](../sessions/S06/self-study.md#exercise-6-predict-then-check). Explain why a homepage `404`, a report `404`, and a curl failure produce different advice. Do not delete a real page to create a failure.
4. Run `bash ~/scripts/site-check.sh` and read the real result for each URL.
5. If the real report is missing, run `~/scripts/maker-report.sh "S5 Report"`, then `build-website`. If the generator was moved, first follow [S6 preflight recovery](../sessions/S06/self-study.md#preflight); do not replace an existing script.
6. Run the checker again, confirm that both pages return HTTP 200, and open both pages in your laptop browser.
7. Run `guide check` to record the completed quest.

The guide checks source shape only. It does not parse Bash, execute learner scripts, observe their output, or prove that either page currently works. Run the syntax and HTTP checks yourself. This core script displays results for a human; its exit code is not an aggregate health result.

## Hints

1. `for page in "" maker-report.html` lets one loop test both paths.
2. Set `base_url="https://lf2607.kolamayermakers.org/~$USER"`, then `url="$base_url/$page"` inside the loop.
3. Reset `curl_exit_code=0` for each page. Capture HTTP with `status=$(curl ...)`, followed by `|| curl_exit_code=$?` to record failure. Then `if [[ "$curl_exit_code" -eq 0 ]]` separates a completed request from a connection failure.
4. Inside that branch, `if [[ "$status" == "200" ]]` selects success. A completed curl command does not by itself mean HTTP 200.
5. Check both `"$page" == "maker-report.html"` and `"$status" == "404"` before printing the report repair with `maker-report.sh` and `build-website`.
6. Preserve other HTTP statuses with a curl inspection hint. For connection failures, print a DNS/connection/TLS hint. Close both `if` blocks with `fi` and the loop with `done`.

## If Check Fails

Compare the source with the self-study script: personal base URL, both loop items, per-page URL, curl status capture, equality tests, report repair output, and closing `fi`/`done`. The source check follows that documented structure, not every equivalent Bash program; it does not require exact message wording. A passing guide check does not replace your manual run.

## Related Reading

- [S6 self-study](../sessions/S06/self-study.md)
- [curl -I](../commands/curl-head.md)
- [HTTP](../concepts/http.md)
- [IP Networking](../concepts/ip-networking.md)
