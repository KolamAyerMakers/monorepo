# S7 Self-Study Guide: HTTP And Multi-Page Sites

Session: S7

## Study Path

1. Add a new Markdown page under `~/src/pages/`.
2. Link it from `index.md` and run `build-website`.
3. Inspect the static URL with `curl -I`.
4. Fetch generated HTML and compare it with the file on disk.
5. Inspect the service URL failure with `curl -v` and explain the missing backend.

## Source To Wire

```text
~/src/pages/setup.md -> build-website -> ~/public_html/setup.html -> HTTP response body
```

The source file is what you edit. The generated HTML is what the static server sends.

## URL Checks

```bash
curl -I https://lf2607.kolamayermakers.org/~username/setup.html
curl -v https://username.lf2607.kolamayermakers.org/
```

Before S8, the service URL should fail because no personal backend service is listening.

## Compare Disk And Network

```bash
curl -L https://lf2607.kolamayermakers.org/~username/setup.html > /tmp/setup-from-web.html
diff ~/public_html/setup.html /tmp/setup-from-web.html
```

No `diff` output means the files match.

## Status Codes

- `200`: the server found and returned the resource.
- `404`: the path does not exist where the server looked.
- `500`: the server failed while handling the request.
- `502`: a proxy could not reach or use the backend service.

## Troubleshooting

- Static URL is `404`: run `build-website`, then check the generated filename in `~/public_html/`.
- Service URL is `502`: expected until your user service exists; no backend is listening yet.
- `curl -I` redirects: retry with `curl -L -I`.
- `diff` shows large differences: compare the correct page and rebuild before fetching again.

## Proof Checklist

- `setup.md` and `setup.html` exist.
- `index.md` links to `setup.html`.
- You can explain the difference between Markdown source and HTTP body.
- You can explain why the service URL fails until your user service exists.

## Docs Pointers

- Read [Platform Reference](../../guides/platform-reference.md) for URL templates.
- Run `man curl`, then search for `-I`, `-L`, and `-v`.
- Run `man diff`, then read the description of no-output success.
- Read the [MDN HTTP status reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status).
