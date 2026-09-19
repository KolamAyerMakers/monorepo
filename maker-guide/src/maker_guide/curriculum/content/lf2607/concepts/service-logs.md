# Service Logs

## Core Idea

Logs are the service telling you what happened.

## Practice Alone

Create and start the independent [sample web service](systemd-user-services.md), including its generated index and unused-port selection. Follow its journal in one terminal:

```bash
journalctl --user -u sample-web.service -f
```

In another terminal on the same machine, request the existing index and an absent path. These commands use the setup card's example port; substitute your chosen port if different. Confirm `missing-example.html` does not exist in your sample directory first, or choose another absent filename.

```bash
curl -i --max-time 5 http://127.0.0.1:18080/
curl -i --max-time 5 http://127.0.0.1:18080/missing-example.html
```

The sample enables Caddy access logs with `--access-log`. Match `request.uri`, `request.method`, `status`, and time (`ts` in JSON) to each request. Read structured fields rather than expecting a fixed text layout. `request.remote_ip` is the direct client; behind a local proxy it may be `127.0.0.1`, not the visitor's address. Startup messages and access logs answer different questions.

A `404` means the server answered but did not find that resource; it is not a crashed process. A directory without an index also returns `404` with browsing disabled. No deletion or broken unit is needed to observe this error. Press `Ctrl-C` to leave the log follower, not stop Caddy, then stop and disable the sample using the setup card's cleanup steps. Do not publish raw logs containing private request data.

## Done When

You can connect a real request to its log entry and distinguish a missing resource from a service failure before changing configuration.

## Go Deeper

- [Logging](logging.md) explains logs beyond service-specific journal output.
- [Service](service.md) explains network services, systemd services, user services, and system services.
- [Time zones](time-zones.md) explains timestamp confusion.
- [journalctl](../commands/journalctl.md) is the command card for reading service logs.
