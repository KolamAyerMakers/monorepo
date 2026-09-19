# Server

## Core Idea

A server is a machine or process that waits for requests and responds to clients.

## Examples

- OpenSSH's `sshd` accepts remote shell connections.
- Caddy can serve files or act as an HTTPS reverse proxy.
- The standalone [sample web service](systemd-user-services.md) runs a user-owned Caddy process serving its generated page over loopback HTTP.
- Forgejo is a git server for source repositories.

## Machine Versus Process

People say "server" in two ways:

- Server machine: the computer reachable on the network.
- Server process: the program listening for requests, such as OpenSSH's `sshd` or Caddy.

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

Run the [sample web service](systemd-user-services.md), then identify the server machine, process, port, protocol, and log command. Stop and disable the sample afterward using that card's cleanup instructions. Explain how a separate shared Caddy could handle public HTTPS while this personal Caddy serves plain HTTP: same software, two processes.

## Docs Pointers

- Run `man sshd`.
- Read [Caddy file-server](../commands/caddy.md).
- Read [Caddy documentation](https://caddyserver.com/docs/).
- Read [Client](client.md) for the other side of the request.
- Read [Service](service.md), [Process](process.md), and [Sockets](sockets.md) for the service process behind a server.
