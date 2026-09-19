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

Start the local demo from the [Caddy file-server card](caddy.md), then connect from another shell on the same machine:

```bash
nc -C -N 127.0.0.1 8000
```

Type these lines, replacing `8000` if you chose another demo port:

```http
GET / HTTP/1.1
Host: localhost:8000

```

Press Enter on a blank line after `Host` to finish the headers. Then press `Ctrl-D` with no pending input to signal EOF. `-C` converts terminal newlines to CRLF; `-N` shuts down the sending side at EOF but continues receiving the reply. The blank line completes the HTTP headers; EOF is not a substitute for it and is not a byte sent as part of HTTP. `Ctrl-C` cancels if you need to start again.

## Automate The Request

After sending it interactively, the same request can come from a script:

```bash
printf '%s\r\n' \
  'GET / HTTP/1.1' \
  'Host: localhost:8000' \
  '' |
  timeout 5s nc -N -w 3 127.0.0.1 8000
```

The request line selects method `GET`, path `/`, and version `HTTP/1.1`. `Host` identifies the hostname and port. `printf` formats each argument with `%s\r\n`, appending carriage return plus line feed (CRLF). The final empty argument produces the blank line ending the headers. This request has no body. Each `\` continues the shell command and must be the last character on its line.

The pipe supplies EOF when `printf` finishes, replacing the interactive `Ctrl-D`. No `-C` is needed here because `printf` already produces CRLF. `Connection: close` is another way to ask the server to close after replying, but is not required in this example. Read the actual status and headers: a redirect is not the requested page, and `nc` will not follow its `Location`.

Change only the path from `/` to `/missing.html`, choosing another name if that file exists. Predict the status, send the request again, and compare it with Caddy's access log and `curl -i http://127.0.0.1:8000/missing.html`. Netcat transmits your message; curl constructs the HTTP request for you.

## Watch Out

- A missing blank terminator can leave the server waiting for more headers.
- `-w` is a connection/idle timeout, not a strict total runtime while data keeps arriving. The outer `timeout 5s` bounds the whole netcat run; use `Ctrl-C` to cancel earlier.
- Plain `nc` to port `443` cannot speak HTTPS. Use [curl](curl.md) for TLS; do not bypass certificate verification.

## Docs Pointers

- Run `man nc` and `help printf`.
- Read [Sockets](../concepts/sockets.md) and [HTTP Basics](../concepts/http-basics.md).
