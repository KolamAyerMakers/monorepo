# Manual Web Service

## Core Idea

A web service is a process listening for network requests.

## Practice Alone

Compute your course personal service port, run a local server, fetch it with `curl`, then stop it and observe failure.

```bash
PORT="$((10000 + $(id -u)))"
python3 -m http.server "$PORT" --bind 127.0.0.1
curl -I "http://127.0.0.1:$PORT/"
```

The manual server keeps the port busy while it runs. Stop it before starting a systemd service on the same port.

The public service URL has this shape:

```text
https://username.lf2607.kolamayermakers.org/
```

Caddy can only make that URL work when your backend process is listening on the expected local port.

## Done When

You can explain why a process must be running for the second URL to work.

## Docs Pointers

- Read [python3 http.server](../commands/python3-http-server.md), [curl](../commands/curl.md), [sockets](sockets.md), and [platform reference](../guides/platform-reference.md).
