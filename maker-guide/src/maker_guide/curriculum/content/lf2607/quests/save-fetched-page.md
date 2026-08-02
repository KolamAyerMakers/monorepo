# Save a fetched page

Quest: save-fetched-page

## Mission

Use `curl` to save a page body into `~/playground/fetch.html`.

## Commands You Will Use

- `curl`
- `>`
- `cat`

## Steps

1. Fetch a small web page with `curl`.
2. Redirect the body into `~/playground/fetch.html`.
3. Use `cat` to confirm the file is not empty.
4. Ask the guide to check the file.

## Hints

1. `curl URL > file` saves the response body.
2. Headers are not required for this quest.
3. Empty files mean the fetch or redirection failed.

## If Check Fails

Fetch again and make sure `~/playground/fetch.html` contains text.

## Related Reading

- [curl](../commands/curl.md)
- [redirection](../commands/redirect.md)
- [external data fetching](../concepts/external-data-fetching.md)
- [HTTP basics](../concepts/http-basics.md)
