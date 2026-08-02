# Sockets

## Core Idea

A socket is an endpoint a process uses to communicate, often over the network with an address, port, and protocol.

## Why Sockets Matter In This Course

- `ssh` opens a client socket to the SSH server.
- `curl` opens a client socket to an HTTP server.
- `python3 -m http.server --bind 127.0.0.1` opens a listening socket on your service port.
- Caddy connects to your user service through a local socket endpoint.

## Client And Listening Sockets

```text
client socket -> network -> listening socket
```

A listening socket waits for incoming connections. A client socket initiates a connection. For your personal service, Python listens on `127.0.0.1:<your-port>`; Caddy connects to that local endpoint when handling the public service URL.

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

Use `curl` to test an HTTP listening socket:

```bash
PORT="$((10000 + $(id -u)))"
curl -I "http://127.0.0.1:$PORT/"
```

## Common Failures

- `Connection refused`: no process is listening on that address and port.
- `Address already in use`: another process is already listening on that port.
- Public URL gives `502`: the reverse proxy could not connect to the backend socket or got a bad response.
- Works on `127.0.0.1` but not publicly: local service is alive, but proxy, DNS, or routing needs checking.

## Proof Check

Start your user service, compute your port with `printf '%s\n' "$((10000 + $(id -u)))"`, then run a local `curl -I` against that port. Explain which process is listening and which command is the client.

## Docs Pointers

- Run `man ss`.
- Run `man 2 socket`.
- Read [IP Networking](ip-networking.md), [Service](service.md), [Server](server.md), [Client](client.md), and [Platform Reference](../guides/platform-reference.md).
