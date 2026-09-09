# python3 -m http.server

## Use

```bash
mkdir -p "$HOME/http-demo"
printf '<h1>Local demo</h1>\n' > "$HOME/http-demo/index.html"
PORT=8000
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$HOME/http-demo"
```

## What It Does

This creates a demo page and serves its directory on port `8000`, listening only on localhost. `--directory` chooses the files explicitly, independently of the shell's current directory.

## Practice

In another shell on the same machine:

```bash
PORT=8000
curl -I "http://127.0.0.1:$PORT/"
```

Inspect the status line. Press `Ctrl-C` in the server terminal to stop it before another process uses that port.

## Watch Out

- Without `--directory`, Python serves the current directory. An unchecked `cd` can fail and accidentally expose unrelated files; prefer the explicit option.
- A missing serving directory does not fall back to the caller's directory; requests for missing files return `404`. Fix the intended directory rather than removing the option.
- Only place public files in the serving directory. Python follows symlinks, so `--directory` is not a filesystem sandbox.
- The loopback bind allows only local connections, but a local reverse proxy can still publish the server to outside visitors.
- This is a learning tool, not a production web server. Use a platform-assigned port when your environment provides one; see the [platform reference](../guides/platform-reference.md) for course routing.
