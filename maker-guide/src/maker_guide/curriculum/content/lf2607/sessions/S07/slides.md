# Run Your Own Web Server

Session: S7

2026-09-19

<!-- end_slide -->

# A Client Asks, A Server Answers

A **client** is a program that sends a request. A **server** is a program that waits for requests and answers them.

```text
client  -- request --> server
client <-- response -- server
```

Your browser is a web client. **Curl is a client too.**

Here, "server" means the running program, not the whole computer.

<!-- end_slide -->

# HTTP Defines The Exchange

A **protocol** defines how programs exchange messages. HTTP defines web requests and responses.

- The client requests a path, such as `/index.html`.
- The server answers with a status, headers, and usually a body such as HTML.

The browser displays the page. Curl prints the response in your terminal.

HTTPS protects this exchange using TLS, which encrypts the connection and verifies the server's identity.

<!-- end_slide -->

# Caddy Already Serves Your Site

**Caddy** is the web-server program already serving your site on the classroom machine.

Today you will run your own Caddy process to learn to start it, request a page, stop it, and recover it without affecting others.

We will connect to it locally first, then from your laptop browser.

<!-- end_slide -->

# Localhost Keeps The Connection Local

`localhost` targets the host **where the client process runs**, using a loopback address: `127.0.0.1` (IPv4) or `::1` (IPv6). The traffic stays inside that host's network stack.

Curl launched in your SSH session runs on the classroom server. A request to `localhost` therefore reaches a service on that server, not on your laptop. We will use `127.0.0.1` explicitly.

We will first ask your server for a page from that same machine.

<!-- end_slide -->

# A Port Selects A Service

An IP address identifies the network destination. A **port** selects a listening service at that address.

- The server **listens** on an address and port.
- The client **connects** to that address and port.

Example: two services on the same host:

```text
127.0.0.1:22    -> SSH server
127.0.0.1:8000  -> HTTP server
```

HTTP uses port `80` by default. Your server will use its own assigned port:

```bash
PORT="$((10000 + $(id -u)))"
```

How does this calculate your port?

<!-- end_slide -->

# Start Your Server

```bash
caddy file-server --listen :$PORT --root ~/public_html --access-log
```

- `--listen` sets the port your server accepts connections on.
- `--root` sets the folder containing the files to serve.
- `--access-log` records requests.

<!-- end_slide -->

# Request A Page With Curl

Open a second SSH connection:

```bash
PORT="$((10000 + $(id -u)))"
curl -i "http://127.0.0.1:$PORT/"
```

`-i` displays the status line and headers before the page's HTML.

**Curl is the client. Your Caddy process is the server.** Both are running on the classroom machine.

In the server terminal, find the access-log record for this request: method `GET`, URI `/`, and its status. You can now see both sides of the exchange.

<!-- end_slide -->

# Reach Your Server Through A Reverse Proxy

The classroom firewall blocks direct external access to your port. How can your laptop browser reach your server?

For your personal service address, shared Caddy is already configured to pass requests to your assigned port and return the responses:

```text
browser -> shared Caddy -> personal Caddy
browser <- shared Caddy <- personal Caddy
```

Shared Caddy is a **reverse proxy**: a server to the browser and a client to personal Caddy. Personal Caddy is the **backend**, the server answering the forwarded request. Same software, two processes with different roles.

<!-- end_slide -->

# Open Your Site From Your Laptop

Open your [service homepage](https://your-handle.lf2607.kolamayermakers.org/) in the laptop browser, replacing `your-handle` with your username.

Look for the same page you just fetched with curl. Watch for the browser's request in your personal Caddy terminal.

Shared Caddy handles the browser's HTTPS connection. Personal Caddy uses local HTTP. Keep the command as given, without `--domain`; no shared configuration changes are needed.

<!-- end_slide -->

# Proxies Can Represent Clients Or Servers

A **proxy** is an intermediary: it forwards requests and sends responses back.

A **forward proxy** represents clients when requesting resources from destination servers.

```text
clients -> forward proxy -> destination servers
```

A **reverse proxy** represents servers, forwarding incoming requests to backends.

```text
clients -> reverse proxy -> backend servers
```

The distinction is which side the proxy represents, not the direction of HTTP. Access filtering and load distribution are examples of proxy uses; our shared Caddy forwards requests to your server.

<!-- end_slide -->

# Follow A Visitor's Request In The Logs

Ask a peer to open your service homepage, then request `/missing.html` on the same hostname.

Watch the first terminal. Find the time or timestamp, `request.method`, `request.uri`, and `status` in the structured access logs.

What client address appears in the log? Can you explain why, even when the request comes from your peer's browser?

<!-- end_slide -->

# Identify The Process Serving Your Page

In the second terminal:

```bash
ps -u "$USER" -o pid,comm,args
```

Which row is your server? Find its **PID**, the process ID, and the command that started it.

What tells you which port and files this process serves?

<!-- end_slide -->

# Match The Process To Its Listening Port

```bash
ss -ltnp "sport = :$PORT"
```

- `-l`: listening sockets.
- `-t`: TCP sockets.
- `-n`: numeric addresses and ports.
- `-p`: process information.

The filter selects your port. Does the PID match the Caddy process you found with `ps`?

A **listening socket** is the endpoint where the server waits for connections.

<!-- end_slide -->

# HTTP Messages Need Line Endings

The names come from typewriters and printing terminals. Starting a new line involved two movements:

- `\r`: **carriage return (CR)**, return to the start of the line.
- `\n`: **line feed (LF)**, advance the paper by one line.

Text formats kept different conventions:

- Unix text files use `\n`.
- Windows text files traditionally use `\r\n`.
- HTTP/1.1 uses `\r\n` to end request and header lines.

A blank line after the last header gives `\r\n\r\n`: the headers are finished.

<!-- end_slide -->

# Send An HTTP Request By Hand

In the second terminal, connect to your server:

```bash
nc -C -N 127.0.0.1 $PORT
```

Type this request, replacing `11234` with your numeric port:

```http
GET / HTTP/1.1
Host: localhost:11234

```

Press Enter on a blank line to end the headers, then `Ctrl-D` with no pending input.

- `GET / HTTP/1.1`: method, requested path, protocol version.
- `Host`: the requested hostname and port.
- `-C` sends HTTP's CRLF (`\r\n`) line endings when you press Enter.
- `-N` finishes sending on end-of-input, while still receiving the reply.

Find your request in Caddy's log. Which parts did curl previously write for you?

<!-- end_slide -->

# Repeat The Request With A Script

Save as `~/scripts/http-request.sh`:

```bash
#!/bin/bash
PORT=$((10000 + $(id -u)))
printf '%s\r\n' \
  'GET / HTTP/1.1' \
  "Host: localhost:$PORT" \
  '' |
  timeout 5s nc -N -w 3 127.0.0.1 "$PORT"
```

Run `bash ~/scripts/http-request.sh`.

`printf` supplies the lines you typed, including the final blank line. When it finishes, the pipe supplies EOF instead of `Ctrl-D`.

<!-- end_slide -->

# Change The Path, Observe The Response

In your script, change only `GET / HTTP/1.1` to `GET /missing.html HTTP/1.1`, then run it again.

Predict the status. Compare the response with the matching entry in Caddy's access log.

Now request the same path with curl:

```bash
curl -i http://127.0.0.1:$PORT/missing.html
```

What is the same? What did curl save you from writing?

<!-- end_slide -->

# What If Two Servers Use The Same Port?

Keep your server running. Try starting another one from the second terminal:

```bash
caddy file-server --listen :$PORT --root ~/public_html --access-log
```

Why did this launch fail? Use `ps` and `ss` to identify the process already listening.

Does the original server still answer curl? Do not change the port or stop the existing process to hide the error.

<!-- end_slide -->

# What If The Server Has No Files?

Stop your server with `Ctrl-C`. In that terminal, serve a new empty practice directory:

```bash
practice_root=$(mktemp -d) &&
caddy file-server --listen :$PORT --root "$practice_root" --access-log
```

Request `/` locally and through your service address. Is the process running? Is the port listening? What do the response and log tell you?

The practice directory is public through the proxy; leave it empty. Your real site files are unchanged.

Stop this server, restart the original command with `--root ~/public_html`, and verify the page is back.

<!-- end_slide -->

# What Happens When Your Server Stops?

If you stop your Caddy process, which of these three URLs will still respond? Why?

```bash
curl -I http://127.0.0.1:$PORT/
curl -I https://$USER.lf2607.kolamayermakers.org/
curl -I https://lf2607.kolamayermakers.org/~$USER/
```

Share your predictions, then press `Ctrl-C` in the terminal running your Caddy process. Run these requests in the second SSH terminal.

Which requests still get a response? Who sends each response?

Start Caddy again with the same command, then repeat the three requests. What changed?

<!-- end_slide -->

# Explain What Runs And What Responds

Explain how you found your server's process and listening socket, what you sent with netcat, and how you distinguished the three incidents.

Confirm the service page works again, then stop your server with `Ctrl-C`. The static site stays available.

This process is not supervised. Keeping it running after logout is the next session's problem.

<!-- end_slide -->

# Next: Keep It Running After Logout

S8: 2026-09-26.

Make Caddy start automatically, keep running after logout, and restart if it crashes.

Use the [self-study route](self-study.md) for complete examples and troubleshooting.

Use `guide` if you need help between sessions.
