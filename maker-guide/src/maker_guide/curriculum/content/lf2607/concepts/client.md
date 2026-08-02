# Client

## Core Idea

A client is the program that initiates a request to a server.

## Course Examples

- `ssh` is a client for the SSH server.
- `curl` is a client for HTTP and other protocols.
- A browser is an HTTP client.
- `git push` uses a git client to talk to a git server.

## Client Questions To Ask

- What server name or address am I contacting?
- What protocol am I using?
- What port is implied or explicit?
- What path, repository, or resource am I asking for?
- What authentication is required?
- What error did the client receive?

## Example

```bash
curl -I https://lf2607.kolamayermakers.org/~username/
```

- Client: `curl`
- Protocol: HTTPS
- Server name: `lf2607.kolamayermakers.org`
- Path: `/~username/`
- Default port: `443`

## Common Confusions

- Client error messages are not always root causes; they are what the client could observe.
- A browser and `curl` can request the same URL but display different levels of detail.
- Authentication failure can be a client key problem, a server account problem, or a permission problem.
- Retrying without reading the error usually wastes time.

## Proof Check

Choose one command from `ssh`, `curl`, or `git push`. Identify the client, server, protocol, and authentication method.

## Docs Pointers

- Run `man ssh`, `man curl`, and `git help push`.
- Read [Server](server.md) for the process receiving the request.
- Read [IP Networking](ip-networking.md) for addresses, ports, and protocols.
