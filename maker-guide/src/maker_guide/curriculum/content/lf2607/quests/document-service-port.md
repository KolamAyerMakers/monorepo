# Document Your Service Port

Quest: document-service-port

## Mission

Improve `setup.md` so you or a peer can find the backend endpoint and understand why that port was chosen. This is optional publishing reinforcement. If `~/src/pages/setup.md` is absent, create it with a heading and link it from `index.md` first, creating source before building. Preserve existing files and links. A separate service page is optional, not another required artifact.

## Calculate And Explain

In your own SSH account on the classroom server:

```bash
id -u
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
micro ~/src/pages/setup.md
```

Preserve existing content. If the computed port exceeds `65535`, ask staff and record the unresolved allocation issue instead of choosing another port. Otherwise add a short section, replacing these example numbers with your own:

```markdown
## My Backend Port

My UID is 1234. The course assigns 10000 + uid, so my backend port is 11234.
This is classroom routing policy, not a general Linux rule.
My personal Caddy listens for plain HTTP on all interfaces at that port.
The classroom firewall blocks new direct external connections to that port.
Shared Caddy handles public HTTPS and forwards to 127.0.0.1 at my assigned port.
Same software, two processes. The static route reads public_html directly
and does not need my personal Caddy process.
```

Explain that `$(id -u)` captures a numeric UID and `$((...))` calculates the sum. Each SSH shell sets its own `PORT`. A systemd `ExecStart` line needs the literal number because it is not evaluated by Bash.

If you have a user unit, document `--listen :YOUR_PORT` with your numeric port, `WorkingDirectory=%h`, the explicit `--root %h/public_html`, and `--access-log`. The publisher replaces the publication directory, so a cwd-only server can retain an old directory. Do not remove the explicit root or change the assigned port.

## Publish And Hand Off

Keep or add `[My setup](setup.html)` on the homepage and `[Home](index.html)` on setup, without replacing existing links. If you already have `service.md`, preserve it and link to the same explanation rather than creating conflicting instructions.

```bash
build-website
```

After success, follow the setup link in your browser through the static route and, when your backend is running, the service route. No server restart is needed. Ask a peer to identify your port and explain which component connects to it. Incorporate useful feedback, naming the peer only with consent.

Use the [source preservation workflow](../sessions/S07/self-study.md#6-preserve-source-now) to review and commit only the changed source files now. Preserve unrelated work and exclude credentials and generated files. The port is public operational information; passwords, private keys, tokens, and private setup links are not.

## Related Reading

- [S7 port arithmetic](../sessions/S07/self-study.md#2-compute-your-port)
- [Enable site.service](enable-site-service.md)
- [Sockets](../concepts/sockets.md)
