# S7 — Run Your Own Web Server

Start a server, match its process to a listening port, and send HTTP yourself. Then distinguish missing content from a stopped server.

**You need:** a built homepage in `~/public_html`, Caddy, curl, `ps`, `ss`, and OpenBSD netcat. Open two classroom SSH shells, or two Ubuntu terminals at home. Call them **server terminal** and **client terminal**.

At home, stop the preview from [Continue at Home](../../guides/continue-at-home.md) with `Ctrl-C` first. If you already completed S8, stop your managed server with `systemctl --user stop site.service`. Only one server can own a given listening address and port.

## 1. Choose your listener

A **client** sends requests; a **server** waits and responds. Your browser and curl are clients. They need not run on a different computer from the server.

`127.0.0.1`, or loopback, means the machine running the command. In an SSH shell, it means the classroom server—not your laptop.

**In class, in both terminals:**

```bash
PORT="$((10000 + $(id -u)))"
LISTEN=":$PORT"
printf 'Port: %s\n' "$PORT"
```

`id -u` gives your numeric user ID; `$((...))` performs arithmetic. UID `1234` gives port `11234`. This is a class convention, not a Linux rule. If the result exceeds `65535`, ask the instructor; do not choose another learner's port.

**At home, in both terminals, use instead:**

```bash
PORT=8080
LISTEN="127.0.0.1:$PORT"
```

Variables belong to one shell; setting them in one terminal does not set them in the other. The home listener is local-only. The class listener uses all interfaces and relies on the classroom firewall to block direct outside access.

## 2. Start and request

**Server terminal:**

```bash
caddy file-server --listen "$LISTEN" --root "$HOME/public_html" --access-log
```

Leave it running. No prompt means Caddy owns the foreground; do not type shell commands into it. Stop it with `Ctrl-C`, **not** `caddy stop` or `caddy reload`, which can target shared Caddy in class.

`--root` selects the published files regardless of your current directory. It is not a sandbox: symlinks can expose files outside that directory. Keep credentials and private symlinks out. `--access-log` records requests.

**Client terminal:**

```bash
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
```

Find the status, headers, and recognizable page content. Then open the page in your browser:

- **In class:** `https://username.lf2607.kolamayermakers.org/`, using your username.
- **At home:** `http://localhost:8080/`. If using a VM, open the browser inside Ubuntu; VM-to-host networking is optional.

### Classroom extension: two routes to the same files

```text
service URL → shared Caddy → personal Caddy → public_html
static URL  → shared Caddy                 → public_html
```

Shared Caddy handles public HTTPS. At your service hostname it acts as a **reverse proxy**, forwarding requests over local HTTP to your process. At `https://lf2607.kolamayermakers.org/~username/`, it reads the files directly.

These are two Caddy processes with different owners and lifecycles. At home there is no shared proxy; only your local server.

## 3. Match requests, processes, and ports

Visit `/missing.html` in your browser, choosing another absent path if needed. In the server terminal, find the request's method, URI, status, and time. Caddy's JSON fields include `request.method`, `request.uri`, `status`, and `ts`.

A missing path should give `404`: the server answered, but the resource was absent. Browsers may also request a favicon or cache responses; use a distinctive path to match your request.

**Client terminal:**

```bash
ps -u "$USER" -o pid,comm,args
ss -ltnp "sport = :$PORT"
```

Find your `caddy file-server` command, its root and port, and its PID. Match it to `pid=...` in the `LISTEN` row.

`ss` options: listeners (`-l`), TCP (`-t`), numeric addresses (`-n`), process information (`-p`, when permitted). `ps` proves a process exists; `ss` proves a listener exists; curl checks a response. None alone proves the whole site works.

In class, public visitors may appear in personal Caddy's logs as `127.0.0.1` because shared Caddy is its direct client. That address does not identify the visitor.

## 4. Send raw HTTP

Curl constructs the request for you. Now do it yourself in the **client terminal**:

```bash
nc -C -N 127.0.0.1 "$PORT"
```

You are now typing into netcat, not the shell. Type these lines, replacing `PORT` with the numeric value:

```text
GET / HTTP/1.1
Host: localhost:PORT

```

Press Enter on the empty line after `Host`. That blank line ends the headers. The request line is method, path, and protocol version; HTTP/1.1 requires a `Host` header. `-C` converts typed newlines to HTTP's CRLF line endings.

Press `Ctrl-D` on an empty input line. This signals EOF; `-N` shuts down sending while still receiving the reply. EOF does not replace HTTP's blank line. If stuck, `Ctrl-C` cancels the client.

Read the response status, headers, blank line, and body. Match it to the server log. Netcat sends plaintext here; do not aim this request at an HTTPS port.

### Save the request

Open `~/scripts/http-request.sh` with Micro, preserving any existing work. Save:

```bash
#!/bin/bash
PORT=$((10000 + $(id -u)))
printf '%s\r\n' 'GET / HTTP/1.1' "Host: localhost:$PORT" '' |
  timeout 5s nc -N -w 3 127.0.0.1 "$PORT"
```

**At home, replace the port assignment with `PORT=8080`.**

`printf` supplies CRLF after each value; the empty value creates the final blank line. The pipe supplies EOF when `printf` finishes. `-w 3` bounds connection/idle waits; `timeout 5s` bounds the whole client run.

```bash
bash ~/scripts/http-request.sh
```

Change only the request path to `/missing.html`, run again, and compare with curl. Both should receive the actual missing-path status. No execute bit is needed when invoking Bash explicitly.

## 5. Incident: running server, wrong root

Predict what an empty root will serve. Stop Caddy with `Ctrl-C` in the **server terminal**, then create a fresh empty directory and launch only if creation succeeds:

```bash
if practice_root=$(mktemp -d); then
  caddy file-server --listen "$LISTEN" --root "$practice_root" --access-log
else
  printf 'Could not create the practice directory. Stop here.\n' >&2
fi
```

Do not add files or symlinks to the practice root. This leaves your real site untouched.

In the **client terminal**, repeat `ps`, `ss`, and local curl. Expect a live process and listener, but `404` for `/`: the root has no index and directory browsing is disabled. Find the request in the log.

In class, check both public routes too: the service route should return `404`, while the static homepage remains available.

Stop the practice server, then restore the real root in the **server terminal**:

```bash
caddy file-server --listen "$LISTEN" --root "$HOME/public_html" --access-log
```

Confirm your actual page is back before the next incident.

<a id="7-predict-stop-and-recover"></a>

## 6. Incident: stopped server

Predict, then stop personal Caddy with `Ctrl-C`. Repeat `ps`, `ss`, and local curl from the client terminal.

| Observation | Expected with personal Caddy stopped |
|---|---|
| `ps` | Its old PID is absent |
| `ss` | No listener on your port |
| Local curl | Connection refused; no HTTP status |
| Classroom service URL | Shared Caddy returns `502` if DNS, TLS, and routing work |
| Classroom static URL | Still serves the published files |

A timeout is not a refusal, and a DNS/TLS error is not HTTP `502`. Record what actually happened. If localhost still answers, identify the process before stopping anything else.

Relaunch the real-root command. Match the new PID to its listener and verify your page in curl and the browser. A restart need not keep the old PID.

## Finish

Stop the manual server with `Ctrl-C` when done. It is not supervised; SSH logout is not an uptime guarantee.

In the server terminal, remove only your empty practice directory with `rmdir -- "$practice_root"`. If the variable was never set or the directory is not empty, inspect rather than recursively deleting.

<a id="5-publish-without-restarting"></a>

## Optional: publish without restarting

While real-root Caddy runs, edit a page under `~/src/pages` and rebuild. In class use `build-website`; at home use `cd ~/src && node scripts/build.mjs`. Reload and find the change: Caddy reads the published tree on new requests, so content updates need no restart.

<a id="6-preserve-source-now"></a>

## Optional: preserve source in Git

From `~/src`, inspect `git status`, `git diff`, and `git diff --cached`. Read untracked files separately; unstaged diff does not show them. Stage exact changed source paths, review the entire staged diff, then commit. Do not include generated output or private logs. Keep unrelated work intact.

## Check yourself

- Match your account, server command, PID, and listening port.
- Explain the HTTP request's CRLF and final blank line.
- Distinguish a wrong-root `404` from connection refusal using your observations.
- In class, explain why static delivery survives a stopped personal server.

[Answers](../../guides/self-study-answers.md#s7-web-server). References: [nc](../../commands/nc.md), [ss](../../commands/ss.md), and [Reverse Proxy](../../concepts/reverse-proxy.md).

## If you get stuck

- Address in use: check `ss`; your S8 service or an old preview may own the port. Stop only your identified process/service.
- Local `404`: inspect `--root`, then the published index. Do not enable browsing to hide missing content.
- Local works, classroom public route fails: bring the local result and public error to support; do not alter shared Caddy, DNS, or TLS verification.
