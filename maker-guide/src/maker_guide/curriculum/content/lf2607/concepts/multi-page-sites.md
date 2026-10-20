# Multi-Page Sites

## Core Idea

A site becomes navigable when pages link to each other.

## Practice Alone

Start the [Caddy card's independent demo](../commands/caddy.md). It supplies a disposable `http-demo` directory and server. In a second terminal, inspect and preserve any existing `about.html`; only create it below if that path is unused:

```bash
printf '<h1>About</h1>\n<a href="/">Home</a>\n' > "$HOME/http-demo/about.html"
```

Edit the demo's `index.html` to include `<a href="/about.html">About</a>`. Open `http://127.0.0.1:8000/`, follow the link, then use Home to return. Substitute your demo port if different; stop the server when finished.

For a Markdown site, follow [First Site Build](first-site-build.md). Its renderer determines how source filenames map to URLs; do not assume the browser requests `.md` files directly.

## Done When

You can reach each page by following links, without typing a guessed URL.
