# Write Site Helper Functions

Quest: write-site-helper-functions

## Optional Mission

Give a repeated read-only service command a memorable name. This is optional shell practice after the backend works, not a prerequisite for a user service or a required `site.sh` dispatcher.

## Try Functions In Your Shell

In your own classroom SSH shell, with `site.service` already created:

```bash
site_status() {
  systemctl --user status site.service --no-pager
}

site_logs() {
  journalctl --user -u site.service --no-pager -n 20
}

site_status
site_logs
```

A definition names commands without running them. Calling the name runs its body. These functions only read state and recent logs; they do not start, stop, or supervise your Caddy. Read the actual service state and request lines rather than treating function execution as proof that the page works.

There is no dispatcher and no arbitrary command execution from supplied arguments. Direct `systemctl` and `journalctl` remain the simplest choice if you do not repeat this enough to need names.

## Keep Only If Useful

The definitions disappear when this shell ends. If you want to preserve them, first inspect any existing file, then save just the definitions above in `~/src/scripts/site-functions.sh`, outside the published pages. Do not overwrite existing content or replace someone else's helper.

```bash
mkdir -p ~/src/scripts
micro ~/src/scripts/site-functions.sh
```

Load your own inspected file into a fresh SSH shell and call a function:

```bash
source ~/src/scripts/site-functions.sh
site_status
```

Sourcing executes a file in your current shell, so source only content you trust and have read. This file needs no executable bit and no `"$@"` dispatcher. Do not change the systemd unit to depend on it; keep the unit's numeric assigned port, all-interface listener, stable `WorkingDirectory=%h`, explicit `--root %h/public_html`, and `--access-log` unchanged.

Use the [source preservation workflow](../sessions/S07/self-study.md#6-preserve-source-now), staging only `scripts/site-functions.sh` for this extension after review. Preserve unrelated work and exclude credentials. No generated files or private backups belong in the commit.

## Explain To A Peer

Ask a peer what calling `site_logs` will do before running it. Explain why reading logs does not change the service lifecycle. If the names made the workflow clearer, add a brief note to existing `setup.md`; otherwise keep using the original commands and skip persistence.

## Related Reading

- [Bash functions](../concepts/bash-functions.md)
- [Watch service logs](watch-service-logs.md)
- [Systemctl](../commands/systemctl.md)
