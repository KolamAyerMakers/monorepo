# Probe a closed port

Quest: probe-closed-port

## Mission

Probe your assigned backend port with `nc` after a controlled stop. Explain the actual result, even if it is unexpectedly open.

## Commands You Will Use

- `nc`

## Steps

1. In your own classroom SSH account, compute the assigned port below. If it exceeds `65535`, stop and ask staff; do not pick another port.
2. [Identify your process and listener](../sessions/S07/self-study.md#identify-your-process-and-listener) before changing anything. Stop only your known foreground server with `Ctrl-C` in its terminal. If your own managed `site.service` owns the port, inspect it and agree to a short interruption before `systemctl --user stop site.service`; record that you must restore it. If ownership is unknown, ask staff and do not stop or kill the process.
3. From another SSH shell on the same classroom machine, compute `PORT` again in that shell and run the bounded probe below while your backend is stopped.
4. Read the actual output and explain what it establishes, not what you hoped it would say.

```bash
PORT="$((10000 + $(id -u)))"
printf '%s\n' "$PORT"
```

Only after confirming the assigned port is valid:

```bash
nc -vz -w 3 127.0.0.1 "$PORT"
```

The numeric loopback endpoint is on the classroom machine, not your laptop. `-z` probes the TCP connection without sending HTTP; `-v` reports the result and `-w 3` bounds the wait.

## Hints

1. Refusal means the connection was rejected, consistent with no listener after your controlled stop. There is no HTTP status.
2. Timeout means no connection completed within the wait; it is not proof of a closed port. Report it separately and ask staff about the unexplained result.
3. Unexpected success means a listener accepted the connection, not that the correct web page works. Compare your own process and listener information with staff; do not kill an unknown process to force a failure.

## Restore The Original Service

If you stopped your manual server, relaunch its original command in its original terminal, using the same assigned port and root; see [Serve a local check page](serve-local-check-page.md). If you stopped the managed unit, restore it with `systemctl --user start site.service` instead of launching a competing server. If the port is unexpectedly occupied, ask staff to help restore the original service safely rather than starting a competitor.

Repeat local curl to confirm recovery and report any unresolved problem. Do not leave a deliberately stopped managed service behind. If no service was running before the probe, there is nothing to restore.

## If Check Fails

Include the observed refusal, timeout, or unexpected open result and explain why that observation supports your diagnosis, or what remains unknown. A keyword list or forced failure is not an explanation.

## Related Reading

- [nc](../commands/nc.md)
- [sockets](../concepts/sockets.md)
- [reverse proxy](../concepts/reverse-proxy.md)
