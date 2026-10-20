# HTML On The Wire

## Core Idea

Your Markdown becomes HTML files, and the web server sends those bytes over HTTP.

## Try it

Start the [Caddy card's local demo](../commands/caddy.md), which creates `http-demo/index.html`. In another terminal on the same machine:

```bash
cat "$HOME/http-demo/index.html"
curl -i --max-time 5 http://127.0.0.1:8000/
```

Use the port you chose for that demo. The response includes headers, a blank line, then the file's HTML body. The browser renders the body; `cat` and curl show its text. Stop the demo with `Ctrl-C` in its server terminal.

For the Markdown-to-HTML step, use the complete setup linked from [First Site Build](first-site-build.md). Markdown source and generated HTML are related, not identical.
