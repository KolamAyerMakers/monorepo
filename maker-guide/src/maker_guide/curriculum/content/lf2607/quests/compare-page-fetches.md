# Compare two page fetches

Quest: compare-page-fetches

## Mission

Fetch two site pages with `curl`, save them, and compare them with `diff`.

## Commands You Will Use

- `curl`
- `diff`
- `>`

## Steps

1. Fetch your homepage into one file.
2. Fetch another page into a second file.
3. Run `diff` on the saved files.
4. Ask the guide to check your command history.

Use your existing homepage and report. Keep the downloaded bodies separate from source and published files:

```bash
mkdir -p ~/playground
curl -fsS --max-time 10 "https://lf2607.kolamayermakers.org/~$USER/" > ~/playground/home-fetch.html
curl -fsS --max-time 10 "https://lf2607.kolamayermakers.org/~$USER/maker-report.html" > ~/playground/report-fetch.html
```

If either fetch fails, stop and repair it before comparing. After both succeed:

```bash
diff ~/playground/home-fetch.html ~/playground/report-fetch.html || [[ $? -eq 1 ]]
```

`diff` returns `1` for different bodies, which is expected here. `||` runs the right-hand test only after a nonzero result; `-eq 1` accepts differences but not a file-reading error. The guide records the whole successful comparison command. Do not use `|| true`, which would also hide real errors.

## Hints

1. Save each response before comparing.
2. Different pages should not be identical.
3. The command history needs both `curl` and `diff`.

## If Check Fails

Run both successful fetches and the complete comparison above before asking again. Diagnose a failed fetch or unreadable file instead of comparing stale output.

## Related Reading

- [curl](../commands/curl.md)
- [diff](../commands/diff.md)
- [HTTP inspection](../concepts/http-inspection.md)
- [HTML on the wire](../concepts/html-on-the-wire.md)
