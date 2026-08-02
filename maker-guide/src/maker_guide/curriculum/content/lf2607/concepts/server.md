# Server

## Core Idea

A server is a machine or process that waits for requests and responds to clients.

## Course Examples

- `lf2607.kolamayermakers.org` is the SSH server you log into.
- Caddy is the web server in front of learner websites.
- Your `site.service` becomes a user-owned web service.
- Forgejo is a git server for source repositories.

## Machine Versus Process

People say "server" in two ways:

- Server machine: the computer reachable on the network.
- Server process: the program listening for requests, such as SSH, Caddy, or Python's HTTP server.

When debugging, ask which meaning is relevant.

## What Servers Need

- An address or name clients can reach.
- A port and protocol.
- A process listening for requests.
- Permissions and configuration.
- Logs that explain failures.

## Common Failures

- DNS works, but no process is listening.
- Process listens locally, but public routing or proxying is missing.
- Service starts, but permissions stop it from reading files.
- Server returns an error, but the client only shows a short symptom.

## Proof Check

For your personal service, identify the server machine, server process, port, protocol, and log command.

## Docs Pointers

- Run `man sshd`.
- Read [Python http.server documentation](https://docs.python.org/3/library/http.server.html).
- Read [Caddy documentation](https://caddyserver.com/docs/).
- Read [Client](client.md) for the other side of the request.
- Read [Service](service.md), [Process](process.md), and [Sockets](sockets.md) for the service process behind a server.
