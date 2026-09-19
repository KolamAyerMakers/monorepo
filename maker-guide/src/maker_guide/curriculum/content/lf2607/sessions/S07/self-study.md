# S7 Self-Study: Run Your Own Web Server

Session: S7

Date: 2026-09-19

## Study Path

Start your own web-server program. Request a page locally with curl, then reach it from your laptop browser. Watch visitors, identify your process and listening port, send raw HTTP, and diagnose two safe incidents before recovering.

Raw HTTP and both incidents are core work. Publishing changes, operating notes, and Git practice remain optional extensions.

## Before You Begin

Use your existing source in `~/src/pages` and published site in `~/public_html`. Do not replace the project or redo the previous session's checker workshop. Open your [static homepage](https://lf2607.kolamayermakers.org/~your-handle/), replacing `your-handle`. If it is missing, run `build-website` in your classroom account and resolve build errors first.

Use the classroom's existing public addresses and shared Caddy configuration. If an address cannot be reached or a browser warns about its certificate, ask the instructor rather than changing shared settings or disabling certificate verification. The instructor must confirm the deployed firewall protection and required tools before this lab. Caddy is expected at `/usr/bin/caddy`; `ss` comes from `iproute2`, and these examples require the OpenBSD `nc` variant from `netcat-openbsd`. Package declarations are not proof that deployment is ready.

From your laptop, open two SSH connections using your actual username:

```bash
ssh username@lf2607.kolamayermakers.org
```

In each, run `whoami` and confirm it agrees with `$USER`. All server commands below run in these SSH shells. Keep your laptop browser available too.

At a classroom shell prompt, confirm the tools are available:

```bash
command -v caddy curl ps ss printf timeout nc mktemp
nc -h
```

The `nc` help should identify Debian's OpenBSD netcat and support `-C`, `-N`, and `-w`. If a tool is missing or the variant differs, ask the instructor to resolve it before continuing; do not install packages with `sudo` or skip the core raw-HTTP lab.

## 1. Client, Protocol, Server

A client is a program that sends a request; a server is a program that waits for requests and answers them. These roles describe programs, not necessarily separate computers. Your browser and curl are both web clients.

A protocol defines how programs exchange messages. HTTP defines web requests and responses: the client requests a path, and the server answers with a status, headers, and usually a body. The browser displays HTML as a page; curl prints what it receives. HTTPS protects the exchange using TLS encryption and server identity verification. You do not need to configure TLS for this exercise.

Shared Caddy already serves your site on the classroom machine. Today you will run your own Caddy process to learn to start it, request a page, stop it, and recover it without affecting others. Shared Caddy forwards your personal service address to your process; this forwarding is called a reverse proxy. Same software, two separate processes.

## 2. Compute Your Port

A port is a number a client uses to select a listening service on a computer. Several server programs can run on the classroom machine; yours needs its own assigned port.

`127.0.0.1` means this computer, also called loopback. In a classroom SSH shell it means the classroom machine; on your laptop it would mean your laptop. We will first connect to personal Caddy from the same machine where it runs.

In the first SSH shell:

```bash
id -u
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
```

`id -u` prints your numeric user ID. `$(id -u)` captures that output; `$((...))` does arithmetic. UID `1234` would give port `11234`. `PORT` stores the result in this shell, not in every open terminal.

The class assigns ports using `10000 + uid`; this is not a general Linux rule. If your result exceeds `65535`, stop and ask the instructor; never pick a spare port or another learner's port.

## 3. Start In The First SSH Shell

If repeating this exercise after S8, inspect your own `site.service` first. Only if it is running and you agree to interrupt it, stop it with `systemctl --user stop site.service`; remember to restore it afterward. The original S7 route needs no unit or tmux.

Start your server:

```bash
caddy file-server --listen ":$PORT" --root "$HOME/public_html" --access-log
```

Keep this terminal visible. There is no shell prompt while personal Caddy owns the foreground. Do not type curl into this running process.

`--listen ":$PORT"` listens for HTTP on all interfaces at your assigned port. The classroom firewall blocks new direct external connections to that port; the listener is not loopback-only. We will explain public access after the local request works. Do not add `--domain`: shared HTTPS is already configured. No Caddyfile or JSON configuration is needed.

`--root "$HOME/public_html"` explicitly selects the published tree regardless of your shell's current directory; never omit it and accidentally serve your home or source tree. It is a file path, not a sandbox: symlinks can lead outside it. Do not publish credentials or symlinks to private files. Without `--browse`, Caddy does not automatically list a directory when its index is missing; restore the source index and build instead.

`--access-log` enables structured request logs. `file-server` disables the personal process's admin API, avoiding an admin-port conflict with shared Caddy. Stop this foreground process with `Ctrl-C` only. Never use `caddy stop` or `caddy reload`: they can target shared Caddy's admin endpoint instead. In S8, use `systemctl --user` to control your supervised process.


## 4. Request And Watch

In the second SSH shell:

```bash
PORT="$((10000 + $(id -u)))"
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
```

`-i` includes response headers with the body; the default request is `GET`. Find the actual HTTP status and recognizable page content. A completed curl command can still show HTTP `404` or `502`. `--max-time 10` bounds the request.

Curl is the client and personal Caddy is the server. Both run on the classroom machine. Confirm this local request works before trying your laptop browser.

### Let The Browser Reach Personal Caddy

The classroom firewall blocks direct external access to personal Caddy's port. Shared Caddy is already configured to pass requests for your personal service address to `127.0.0.1` at your assigned port and return its responses:

```text
browser -> shared Caddy -> personal Caddy
browser <- shared Caddy <- personal Caddy
```

This intermediary role is called a reverse proxy. Personal Caddy is the backend, the server answering the forwarded request. Shared Caddy acts as a server to the browser and as a client to personal Caddy. Shared Caddy handles public HTTPS and uses HTTP locally to reach personal Caddy; the classroom configuration is already in place. These are two processes running the same software, not two different server products.

Open your [service homepage](https://your-handle.lf2607.kolamayermakers.org/) in the laptop browser, replacing `your-handle` with your username. Look for the same page. The static address with `/~username/` still works differently: shared Caddy reads `public_html` itself instead of asking personal Caddy. Both serve the same published files.

If the local request works but the public address does not, keep the error and ask the instructor. HTTP `502` means shared Caddy could not obtain a usable response from personal Caddy. A name-resolution error means the address could not be looked up; a certificate error concerns the secure connection. These are not HTTP `502` responses. Do not change shared settings or bypass certificate verification.

Ask a peer to open your service homepage, then visit `/missing.html` on that same hostname. Choose another nonexistent path if you already have that file. In the structured access logs, find `request.method`, `request.uri`, `status`, and the timestamp or time (`ts` in JSON). Terminal formatting can differ from JSON captured in the journal later; read the fields rather than expecting a fixed line layout. Match those requests to the peer's actions; browsers may also ask for a favicon or reuse cached content.

Personal Caddy may log `127.0.0.1` for public visitors because its direct client is shared Caddy. That address does not identify which peer visited. The missing path should return `404`: the backend answered, but the resource was absent. Agree a distinctive path and time with your peer rather than guessing which log line is theirs.

## Identify Your Process And Listener

Keep Caddy running in the first SSH shell. In the second, reuse the exact process command from S3:

```bash
ps -u "$USER" -o pid,comm,args
```

`-u "$USER"` selects processes owned by your account. Find the `caddy file-server` command with your assigned port and published root. Read its process ID (`PID`), command name (`COMMAND`), and full arguments (`COMMAND` in the last column). Note that PID before changing anything; a process named `caddy` alone is not enough to identify your server.

Now inspect listening TCP sockets:

```bash
ss -ltnp "sport = :$PORT"
```

`-l` selects listeners, `-t` TCP, `-n` numeric addresses and ports, and `-p` process information where permitted. The filter selects your local listening port. Find `LISTEN`, your port under the local address, and `pid=...` in the process information. A wildcard address such as `*` or `[::]` is consistent with the all-interface launch, not a loopback-only listener.

Match that PID to the Caddy row in your account's `ps` output. Together they connect ownership, running command, and listening port. `ps` alone does not prove a listener exists, and `LISTEN` alone does not prove the correct page is served. If the PID is missing or does not match, keep the output and ask the instructor; do not use sudo or stop an unknown process.

## Send Raw HTTP

Curl constructs HTTP for you. First send a request interactively while the same server runs. In the second SSH shell:

```bash
nc -C -N 127.0.0.1 $PORT
```

Now you are typing into netcat, not the shell. Type these request lines using your numeric port in place of `PORT` below. Netcat does not expand shell variables in the text you type:

```text
GET / HTTP/1.1
Host: localhost:PORT

```

The request line has three parts: method `GET`, path `/`, and protocol version `HTTP/1.1`. The `Host` header names the requested host and port; HTTP/1.1 requires it.

After the `Host` line, press Enter on a blank line to end the headers. This GET has no request body. `-C` converts terminal newlines to HTTP's CRLF line endings. The response can arrive as soon as that blank line is sent.

Press `Ctrl-D` with no pending input. This signals end-of-input (EOF) to netcat; `-N` then shuts down the sending side of its connection while continuing to receive the reply. EOF does not replace the HTTP blank line and is not an HTTP character. If you get stuck, `Ctrl-C` cancels this client; reconnect to try again.

Read the response status line, headers, blank line, and page body. Match `GET /` and its status to the access log in the first terminal. `Connection: close` would also ask the server to close after replying, but this exercise uses EOF instead. Netcat sends plaintext, not TLS; target your own loopback HTTP port, not shared Caddy's HTTPS port.

### Save The Same Request In A Script

In the second SSH shell, inspect any existing file before editing it:

```bash
mkdir -p ~/scripts
micro ~/scripts/http-request.sh
```

Preserve an existing script rather than overwriting unrelated work. Save this small script:

```bash
#!/bin/bash
PORT=$((10000 + $(id -u)))
printf '%s\r\n' \
  'GET / HTTP/1.1' \
  "Host: localhost:$PORT" \
  '' |
  timeout 5s nc -N -w 3 127.0.0.1 "$PORT"
```

`printf` supplies the lines you typed. `%s\r\n` prints each argument followed by CRLF, and the final empty string produces the blank line. Double quotes expand `$PORT` in `Host`. Each backslash continues the command; put nothing after it. A newline after `|` also continues the pipeline.

When `printf` finishes, its pipe supplies EOF instead of your interactive `Ctrl-D`. Keep `-N`; no `-C` is needed because `printf` already emits CRLF. `-w 3` bounds connection and idle waits; `timeout 5s` bounds the whole netcat run. Interactive typing has no short timeout, so you have time to enter the request.

Run `bash ~/scripts/http-request.sh` and compare its response and access log with your interactive request. No executable bit or new checker is needed.

### Change Only The Path

Predict the response for `/missing.html`. Confirm this file is absent from your published site; if it exists, choose an unused path rather than changing any real file. In `http-request.sh`, change only `GET / HTTP/1.1` to `GET /missing.html HTTP/1.1`. Keep the method, version, headers, address, and port unchanged, then run the script again. You can also repeat the request in a fresh interactive netcat connection.

Inspect the actual status and find `request.uri` `/missing.html` with status `404` in the server log. The server is answering; the requested file is missing. Neither a `404` nor a listening socket alone describes the whole service.

Compare with `curl -i http://127.0.0.1:$PORT/missing.html`: what did curl construct for you?

## Incident 1: A Running Server With The Wrong Root

Predict what happens when Caddy listens correctly but serves an empty directory. Do not delete or rename any website files. Press `Ctrl-C` in the first SSH shell to stop the original server. In that SAME first/server shell, create a fresh empty practice directory and launch only if creation succeeds:

```bash
if practice_root=$(mktemp -d); then
  caddy file-server --listen :$PORT --root "$practice_root" --access-log
else
  printf '%s\n' 'Practice directory creation failed. Stop and ask the instructor.' >&2
fi
```

`mktemp -d` creates a new directory and prints its path; the assignment stores it in this shell. The `if` prevents Caddy from starting with an empty or invalid root after creation fails. If it fails, do not continue the incident; restore the published-root command below and ask for help. Never substitute your home, source, or an existing temporary directory. Treat this fresh directory as public while served, even though it is under `/tmp`; put no secrets or private symlinks in it. Keep it empty and do not enable browsing.

In the second SSH shell:

```bash
ps -u "$USER" -o pid,comm,args
ss -ltnp "sport = :$PORT"
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
curl -i --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
curl -I --max-time 10 "https://lf2607.kolamayermakers.org/~$USER/"
```

Identify the new Caddy PID, its temporary `--root`, and the matching `LISTEN` socket. Expect local and public service `404` responses: the empty root has no index. Find those requests and statuses in the first terminal's access log. The process, listener, and fresh log records show a live server with missing content, not a stopped backend. Shared Caddy still serves the real static site from untouched `public_html`; confirm it in the laptop browser too.

Before the next incident, press `Ctrl-C` in the first shell and restore the original root there:

```bash
caddy file-server --listen :$PORT --root ~/public_html --access-log
```

Repeat local curl in the second shell and reload the public service homepage. Confirm the real page and its request logs are back before deliberately stopping it again. Leave the empty practice directory alone until cleanup.

<a id="7-predict-stop-and-recover"></a>

## 5. Predict, Stop, And Recover

This is incident 2. With the published root restored, predict with your peer what the direct loopback request, public service hostname, and public static homepage will do when only your backend stops. Make your predictions before reading the expected results below.

Press `Ctrl-C` in the first terminal to stop your personal Caddy process. From the second terminal:

```bash
ps -u "$USER" -o pid,comm,args
ss -ltnp "sport = :$PORT"
curl -i --max-time 10 "http://127.0.0.1:$PORT/"
curl -i --max-time 10 "https://$USER.lf2607.kolamayermakers.org/"
curl -I --max-time 10 "https://lf2607.kolamayermakers.org/~$USER/"
```

Record your actual observations first, then compare them with these expectations:

| Route | Expected with the backend stopped |
| --- | --- |
| Direct loopback request | Connection refused, with no HTTP status |
| Public service hostname | HTTP `502` if DNS, TLS, and the proxy route work |
| Public static homepage | Continues serving the published site |

Your stopped Caddy PID should be absent from `ps`, and `ss` should have no listener row for your port. The local refusal comes from trying to connect to a port with no listener; personal Caddy cannot log that request. Public `502` is an HTTP response from shared Caddy when it cannot obtain a usable backend response. A `502` by itself does not prove that the process is stopped; the paired local observations narrow the cause. Static delivery does not depend on personal Caddy.

Record what actually happened, including unexpected outcomes. A timeout is not a refusal; DNS and TLS errors are not HTTP statuses. If localhost still answers, identify the server before stopping anything else.

In the first terminal, relaunch:

```bash
caddy file-server --listen ":$PORT" --root "$HOME/public_html" --access-log
```

Repeat `ps`, `ss`, and local curl, then reload the service homepage in the laptop browser. Match the relaunched process to its listener; do not assume a restart keeps the old PID. Ask your peer to visit again and match their request to the terminal log. Leave no deliberately broken state behind.

## 6. Explain And Finish

Explain which process answers each address, how its PID connects your account to the listening port, and how you recognized a request in the log. Describe your raw request's line endings and final blank line. Distinguish a running server with the wrong root from a stopped backend using actual observations. Confirm the service page works again after relaunching. No new page, published notes, or Git commit is required for this experiment.

After any optional exercises below, stop the manual server with `Ctrl-C`. It is not supervised, and SSH logout behavior is not an uptime guarantee. If you temporarily stopped an existing S8 unit, stop the manual server first, restore it with `systemctl --user start site.service`, and confirm local and public access again.

In the first shell, if you created the practice directory, remove only that empty directory with `rmdir -- "$practice_root"`. If the variable is unset or the directory is no longer empty, leave it and ask for help; do not use recursive deletion.

<a id="5-publish-without-restarting"></a>

## Optional: Publish Without Restarting

For extra practice, change your homepage or keep useful operating notes in `setup.md`. This is not required for the server exercise. Use the second SSH shell while personal Caddy keeps running:

```bash
micro ~/src/pages/setup.md
micro ~/src/pages/index.md
```

In micro, `Ctrl-S` saves and `Ctrl-Q` exits. Preserve existing content and links. If you want a new setup page, adapt this example using your own port and observations:

```markdown
# My Setup

My UID is 1234, so my course port is 10000 + 1234 = 11234.
Shared Caddy forwards my service address to my personal Caddy process.
Stopping my process leaves the static site available.

    PORT="$((10000 + $(id -u)))"
    caddy file-server --listen ":$PORT" --root "$HOME/public_html" --access-log

I stop my foreground server with Ctrl-C in its terminal.

[Home](index.html)
```

Link the page from the homepage with `[My setup](setup.html)`. Keep passwords, tokens, private keys, and private connection links out of public notes. Ask before naming peers.

After editing source, publish:

```bash
build-website
```

After a successful build, reload your page through the personal service address without restarting Caddy. The explicit `--root` follows the replaced `public_html` directory on new requests. Do not edit generated HTML. If the browser shows an old copy, try a fresh reload before changing the server.

<a id="6-preserve-source-now"></a>

## Optional: Preserve Source In Git

If you changed source files, preserve only those changes in the existing `~/src` repository. The paths below assume you edited both `index.md` and `setup.md`; omit any path you did not create or change. If the repository is absent, initialize it once with `git -C ~/src init`, not in your home or published directory.

```bash
git -C ~/src status
git -C ~/src diff -- pages/index.md pages/setup.md
git -C ~/src diff --cached
```

Read new files in the editor; unstaged diff does not show untracked content. If unrelated work is staged, preserve it and ask for help separating changes. Otherwise:

```bash
git -C ~/src add -- pages/index.md pages/setup.md
git -C ~/src diff --cached
```

Only if the entire staged diff contains the intended changes and no credentials:

```bash
git -C ~/src commit -m "Document my web server"
git -C ~/src status
```

Do not use `git add .` or stage generated output. There is no required commit or push when you have not changed any source.

## Troubleshooting

- Local curl is refused: confirm personal Caddy is still running, the shell's `PORT` is correct, and both SSH sessions are on the classroom machine.
- Local HTTP is `404`: inspect the running command's `--root` first. After the empty-root incident, stop your practice server and restore `~/public_html`. Otherwise inspect the published path and source, including `index.md` for the homepage, then build. Do not remove `--root` or enable browsing to hide the error.
- Local access works but public access fails: compare your port with the course formula, then bring the local result and public error to the instructor. Do not alter DNS, shared Caddy, or TLS verification.
- A change is missing: save the source, resolve build errors, and reload freshly. A routine content edit is not a reason to restart personal Caddy.
- Static access works while the service route is `502`: the files may be fine while the backend is absent or unreachable. Diagnose the backend separately.

## Further Reading

- [Serve a local check page](../../quests/serve-local-check-page.md)
- [Diagnose the service URL](../../quests/diagnose-second-url.md)
- [Caddy file-server command](https://caddyserver.com/docs/command-line#caddy-file-server)
- [Reverse proxy](../../concepts/reverse-proxy.md)

## Next Session

S8: **2026-09-26**, Keep Your Server Running. Restart the manual backend, then let a systemd user service own its lifecycle.
