# Sockets

## Core Idea

A socket is an endpoint a process uses to communicate, often over the network with an address, port, and protocol.

## Examples

- `ssh` opens a client socket to the SSH server.
- `curl` opens a client socket to an HTTP server.
- The [Caddy file-server demo](../commands/caddy.md) opens a listening socket on loopback port `8000`.
- A separate reverse proxy can connect to a file server through a local socket endpoint.

## Client And Listening Sockets

```text
client socket -> network -> listening socket
```

A listening socket waits for incoming connections. A client socket initiates a connection. In the standalone demo, Caddy listens on `127.0.0.1:8000` and curl connects to it over plain HTTP. In a proxied deployment, a shared Caddy process can accept public HTTPS and connect to a personal Caddy HTTP listener: the same software, two processes with different sockets.

## Address And Port

```text
127.0.0.1:14567
|         |
address   port
```

`127.0.0.1` means localhost from the machine's point of view. The port selects the service endpoint on that address.

## Commands To Try

Run `ss` to inspect listening and connected sockets:

```bash
ss -ltnp
ss -tnp
```

Start the [Caddy demo](../commands/caddy.md), including its generated page and unused-port inspection. In a second shell on the same machine, use `curl` to test its HTTP listening socket. Substitute the demo's chosen port if different:

```bash
PORT=8000
curl -I "http://127.0.0.1:$PORT/"
```

## Common Failures

- `Connection refused`: no process is listening on that address and port.
- `Address already in use`: another process is already listening on that port.
- Public URL gives `502`: the reverse proxy could not connect to the backend socket or got a bad response.
- Works on `127.0.0.1` but not publicly: local service is alive, but proxy, DNS, or routing needs checking.

## Proof Check

Run the local request above and explain which process is listening and which command is the client. Stop the demo with `Ctrl-C` in its server terminal, then repeat curl and compare the connection result. Do not stop an unknown listener.

## Docs Pointers

- Run `man ss`.
- Read [ss](../commands/ss.md) to match a listener to its process.
- Run `man 2 socket`.
- Read [IP Networking](ip-networking.md), [Service](service.md), [Server](server.md), and [Client](client.md).
