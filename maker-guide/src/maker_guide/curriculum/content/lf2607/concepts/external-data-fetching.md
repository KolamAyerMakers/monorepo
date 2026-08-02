# External Data Fetching

## Core Idea

External data fetching means a script asks a network service for data, saves the response, and uses it as input for local work.

In this course, the local work is usually publishing a small fetched response into a Markdown page.

## Safe Pattern

```bash
curl -L https://example.org > ~/playground/example.html
```

Inspect before publishing:

```bash
head ~/playground/example.html
file ~/playground/example.html
```

Then write a small Markdown page and rebuild.

## Questions To Ask

- What URL did the data come from?
- Did the request follow redirects?
- Is the response text, HTML, JSON, or binary data?
- Where did you write it locally?
- Can you rebuild the page without manually copying output?

## Watch Out

Do not fetch huge data blindly into your site. Start with small text endpoints and inspect headers with `curl -I`.

## Docs Pointers

- Read [curl](../commands/curl.md), [curl -I](../commands/curl-head.md), [HTTP](http.md), [client](client.md), [file encoding](file-encoding.md), and [filesystem as CMS](filesystem-as-cms.md).
