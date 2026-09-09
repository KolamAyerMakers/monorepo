# nc

## Use

```bash
nc -vz -w 3 127.0.0.1 65534
```

This probes one TCP port on the same machine. `65534` is an example: use a local port you expect to be unused, not a range of ports.

## What It Does

`nc` (netcat) connects standard input and output to a TCP connection. It does not add HTTP headers, follow redirects, or negotiate TLS.

- `-v`: print connection diagnostics.
- `-z`: probe the connection without sending application data.
- `-w 3`: limit connection and idle waits to three seconds.
- `127.0.0.1`: IPv4 loopback, the same machine.

## Closed-Port Practice

A port without a listener normally returns "Connection refused" and a nonzero exit status. A timeout can instead mean filtering or another connectivity problem; it does not prove a closed port. If the connection succeeds, something is listening: choose another unused port rather than stopping that service.

This is a TCP diagnostic, not an HTTP request. A refused connection has no HTTP status code.

## Plaintext HTTP

Start the local demo from the [Python HTTP server card](python3-http-server.md). With that server still running on port `8000`, send a complete request from another shell on the same machine:

```bash
printf 'GET / HTTP/1.1\r\nHost: localhost:8000\r\nConnection: close\r\n\r\n' | nc -w 3 127.0.0.1 8000
```

The request line selects method `GET`, path `/`, and version `HTTP/1.1`. `Host` identifies the hostname and port. `printf` emits carriage return plus line feed (CRLF) for each `\r\n`; the final pair creates the blank line that ends the headers. This request has no body.

`Connection: close` asks the server to close after responding. Read the actual status and headers: a redirect is not the requested page, and `nc` will not follow its `Location`.

## Watch Out

- A missing blank terminator can leave the server waiting for more headers.
- `-w` is a connection/idle timeout, not a strict total runtime while data keeps arriving. Use `Ctrl-C` to cancel.
- Plain `nc` to port `443` cannot speak HTTPS. Use [curl](curl.md) for TLS; do not bypass certificate verification.
- Netcat variants have different flags. Read your local `man nc`; do not assume listener examples for another variant apply.

## Docs Pointers

- Run `man nc` and `help printf`.
- Read [Sockets](../concepts/sockets.md) and [HTTP Basics](../concepts/http-basics.md).
