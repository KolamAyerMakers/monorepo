# Manual Web Service

## Core Idea

A web service is a process listening for network requests.

## Practice Alone

Follow the complete [Caddy file-server example](../commands/caddy.md): create its demo directory, serve that explicit root over loopback HTTP in one shell, and request it with curl from a second shell. The foreground server occupies the first shell until you stop it with `Ctrl-C`. No configuration file is needed; do not use `caddy stop` or `caddy reload`.

The manual server keeps the port busy while it runs. Stop it before starting a systemd service on the same port.

A reverse proxy can forward public requests to a loopback listener. Binding to loopback does not guarantee privacy when a proxy exposes the port: serve only the intended directory. Use your platform's assigned port and routing rules when moving from the standalone example to a published service.

## Done When

You can explain why a backend process must be running for a proxy to return its content, and why stopping the process changes the client's result.

## Docs Pointers

- Read [Caddy file-server](../commands/caddy.md), [curl](../commands/curl.md), and [sockets](sockets.md).
