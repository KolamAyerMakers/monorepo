# External Data Fetching

Download into a separate file, validate it, then replace the last good result. Redirecting directly onto the good file destroys it before the request succeeds.

## Try it

This example uses a fresh temporary directory, so it cannot replace your existing work:

```bash
work=$(mktemp -d)
printf 'Previous good page\n' > "$work/page.html"
if curl -fLsS --max-time 10 https://example.org/ -o "$work/download.html" && [[ -s "$work/download.html" ]]; then
  mv "$work/download.html" "$work/page.html"
else
  printf 'Download failed or was empty; previous page kept.\n' >&2
fi
head "$work/page.html"
```

On success, inspect the fetched HTML. To practise failure, rerun the full example with `https://example.invalid/`; the last command should still show `Previous good page`. The `.invalid` domain is reserved for names that do not resolve.

`-f` rejects HTTP errors, `-L` follows redirects, `-sS` keeps error messages, and `--max-time` bounds the request. Nonempty content is only a basic check: for JSON, also validate required fields and types with [jq](../commands/jq.md) before replacing the output.

Only rebuild or publish after the required download and validation succeed. Keep credentials out of URLs and logs; never execute downloaded data as shell commands.

## Related reading

- [curl](../commands/curl.md), [HTTP](http.md), and [file encoding](file-encoding.md)
