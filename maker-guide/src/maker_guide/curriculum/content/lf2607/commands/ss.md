# ss

## Use

```bash
ss -ltnp
```

## What It Does

`ss` shows sockets, the endpoints processes use to communicate. It is provided by the `iproute2` package.

- `-l`: show listening sockets.
- `-t`: select TCP sockets.
- `-n`: show numeric addresses and ports instead of resolving names.
- `-p`: show process information when your account can access it.

## Practice

Start the [Caddy file-server demo](caddy.md), which creates a public practice page and listens on an unused loopback port. In a second shell, select that port; replace `8000` if you chose a different port for the demo:

```bash
PORT=8000
ss -ltnp "sport = :$PORT"
ps -u "$USER" -o pid,comm,args
curl -I "http://127.0.0.1:$PORT/"
```

`sport` filters the local socket port. Find the `LISTEN` state, local address and port, and process PID. Match that PID to your own Caddy row in `ps`. The socket identifies where connections arrive; the process handles them.

Stop your demo with `Ctrl-C` in its terminal, then repeat `ss` and curl. With no other listener, the matching socket disappears and the connection is refused.

## Watch Out

- A listening socket does not prove a working page. Inspect an actual HTTP response too.
- A port filter is not an ownership check. Match the PID with processes owned by your account; do not stop another user's process.
- Process details may be hidden for other users or by host policy. Missing details are not proof that no process exists and are not a reason to use `sudo`.
- `ss` is a snapshot, not a continuous monitor. Run it again after a change.

## Docs Pointers

- Run `man ss`.
- Read [Sockets](../concepts/sockets.md), [Processes](../concepts/process.md), and [ps](ps.md).
