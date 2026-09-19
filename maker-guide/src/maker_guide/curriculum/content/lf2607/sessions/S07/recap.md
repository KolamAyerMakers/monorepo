# S7 Recap: Run Your Own Web Server

Session: S7

Date: 2026-09-19

## Client And Server

A client sends a request; a server waits for requests and answers. Your browser and curl are clients. A server here means a running program, not the whole computer.

HTTP is the protocol, the rules for those requests and responses. HTTPS protects the exchange using TLS. Shared Caddy already serves your static site. You started a personal Caddy process to learn start, request, stop, and recovery without affecting others. Same software, two separate processes.

You first used curl on the classroom machine to request a page directly from personal Caddy. `127.0.0.1` means that same machine; the port selects your listening service.

## From Browser To Personal Caddy

For your personal service address, shared Caddy forwards requests to personal Caddy and returns its responses. That role is a reverse proxy. Personal Caddy is the backend, the server behind it. Shared Caddy acts as a server to your browser and a client to personal Caddy.

```text
Browser -> HTTPS -> shared Caddy -> HTTP on 127.0.0.1:PORT -> personal Caddy -> public_html
Browser -> HTTPS -> shared Caddy -> public_html (static /~username/ route)
```

The static address uses the same published files without your personal Caddy process. Shared Caddy handles public HTTPS; ask the instructor about its configuration, do not change it. Personal Caddy serves plain HTTP without `--domain`.

## Start And Observe

In your first SSH shell on the classroom machine:

```bash
PORT="$((10000 + $(id -u)))"
caddy file-server --listen ":$PORT" --root "$HOME/public_html" --access-log
```

The port formula is course policy. If the result exceeds `65535`, ask the instructor rather than choosing another port. The listener uses all interfaces; the classroom firewall blocks new direct external connections to that port. Keep the explicit `--root`; never serve your home or source directory. The root is not a sandbox: symlinks can expose files outside it. Without `--browse`, a missing index does not produce an automatic directory listing.

In a second SSH shell:

```bash
PORT="$((10000 + $(id -u)))"
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
```

Then open your [service homepage](https://your-handle.lf2607.kolamayermakers.org/) in the laptop browser, replacing `your-handle`. `--access-log` records structured fields: `request.method`, `request.uri`, `status`, and a timestamp or time (`ts` in JSON). Match them to your own and a peer's requests; terminal and journal formatting can differ. Personal Caddy sees shared Caddy's loopback connection, so the logged address need not be the visitor's address.

## Identify The Process And Port

After watching visitors, reuse S3's process command in the second SSH shell, then inspect the listener:

```bash
ps -u "$USER" -o pid,comm,args
ss -ltnp "sport = :$PORT"
```

Find your `caddy file-server` arguments in `ps`, which selects processes owned by your account. Match that row's PID to `pid=...` in `ss`, alongside `LISTEN` and your assigned local port. `-ltnp` selects listening TCP sockets, numeric addresses/ports, and available process details. A process alone does not prove a listener exists; a listener alone does not prove the page is correct. Missing or unexpected ownership information is a reason to ask for help, not kill a process.

## Build A Raw Request

Raw HTTP is core S7 work. These are the request lines, with `PORT` standing for your assigned number and a blank line after the headers:

```text
GET / HTTP/1.1
Host: localhost:PORT

```

The request line gives method, path, and version. `Host` names the requested authority and is required in HTTP/1.1. Lines end with CRLF (`\r\n`); the final blank line ends the headers.

While your backend runs, connect from the second SSH shell:

```bash
nc -C -N 127.0.0.1 $PORT
```

Type the request using the actual numeric port, press Enter on a blank line, then `Ctrl-D` with no pending input. `-C` converts newlines to CRLF; `-N` finishes sending at EOF while still receiving the response. EOF is not the blank line ending HTTP headers, and typed text inside netcat does not expand `$PORT`.

Then save the same request as `~/scripts/http-request.sh`, preserving any existing file:

```bash
#!/bin/bash
PORT=$((10000 + $(id -u)))
printf '%s\r\n' \
  'GET / HTTP/1.1' \
  "Host: localhost:$PORT" \
  '' |
  timeout 5s nc -N -w 3 127.0.0.1 "$PORT"
```

Run `bash ~/scripts/http-request.sh`. Each string gets its own CRLF; `''` produces the final blank line. The pipe supplies EOF when `printf` finishes, replacing `Ctrl-D`. No `-C` is needed in the script. `-w 3` limits connection/idle waits; `timeout 5s` bounds the scripted exchange. The classroom uses Debian's OpenBSD netcat; tool availability and flags need instructor preflight.

Read the status, headers, and body, then find the matching log entry. Change only `/` to `/missing.html` in the request line and repeat. For an absent file, expect `404` in both response and log, not a connection failure. Do not modify a real file to manufacture this result. The [raw-HTTP lab](self-study.md#send-raw-http) builds the request incrementally.

<a id="what-stopping-changes"></a>

## Three Safe Incidents

`file-server` disables the personal process's admin API. Never use `caddy stop` or `caddy reload`: they can target shared Caddy's admin endpoint. When an incident calls for stopping, use `Ctrl-C` only in your own server's terminal. Keep the original running for the first incident:

| Incident | Evidence and recovery |
| --- | --- |
| Start an identical second Caddy in the second SSH shell while the first runs | Startup reports an occupied address; `ss` still matches the original PID, curl still works, and the first terminal logs the request. The second launch failed, not the original server. |
| Stop the first server, then serve a fresh empty practice root in that same first shell | `ps` shows the temporary root and new PID; `ss` matches it. Local and public service requests return `404` with fresh logs while the real static site works. Stop this process and restore `~/public_html` before proceeding. |
| Stop the restored backend in the first shell | Its PID and listener disappear. Local curl is refused with no HTTP status; the public service returns shared Caddy's `502` if routing works; the static site still loads. Restart and verify recovery. |

Use the [guarded empty-root procedure](self-study.md#incident-2-a-running-server-with-the-wrong-root): `practice_root=$(mktemp -d)` belongs in the first/server shell, and Caddy must not launch if creation fails. Treat that fresh directory as public and keep it empty; never delete or rename real website files, serve private files, or enable directory browsing.

After the practice server stops, restore in the first shell:

```bash
caddy file-server --listen :$PORT --root ~/public_html --access-log
```

In the second shell, compare the three routes:

```bash
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
curl -i --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
curl -I --max-time 10 "https://lf2607.kolamayermakers.org/~$USER/"
```

Repeat `ps` and `ss` after recovery and match the new process to its port. Confirm the real page locally and in the laptop browser, plus a matching request log. A `502` alone does not prove a stopped process. DNS failures, certificate failures, and timeouts are different results. Report actual observations; do not change ports, stop unknown processes, or bypass TLS to manufacture success.

## Finish

Success means you can connect ownership, PID, listening port, HTTP response, and request log, then distinguish and recover all three incidents. No new page or Git commit is required. After confirming recovery, stop the foreground server with `Ctrl-C`; it is not an uptime promise. Remove only your empty practice directory with `rmdir -- "$practice_root"` in the first shell if that variable still identifies it. If it is unset or the directory is not empty, leave it and ask for help. Restore any pre-existing S8 user service you temporarily stopped, following the self-study cleanup.

## Optional Practice

If useful, keep operating notes in `setup.md`, publish a content change while Caddy runs, and preserve your source in Git. The [self-study extensions](self-study.md#optional-publish-without-restarting) provide the steps. These are extra practice, not live-session deliverables. Keep secrets out of published notes and preserve unrelated work.

## Questions To Keep

- Which process answers local curl, and which handles public HTTPS?
- Why does each SSH shell need its own `PORT` assignment?
- Why is a missing path different from a missing listener?
- Why can a public request appear as `127.0.0.1` in the backend log?
- How do `ps` and `ss` identify your own server rather than another Caddy process?
- What ends the HTTP headers, and how is that different from `Ctrl-D` and EOF?
- How can the service homepage return `404` while the static homepage still works?

The [self-study route](self-study.md) includes complete raw-HTTP and incident procedures. Extra body comparisons, tmux, and helper scripts are not required outcomes here.

## Next Session

S8: **2026-09-26**, Keep Your Server Running. A user service will take over the process lifecycle.
