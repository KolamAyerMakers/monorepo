# Write Site Helper Functions

Quest: write-site-helper-functions

## Optional Mission

Give a repeated service command a memorable name. A **function definition** names commands without running them; calling that name runs its body.

## Try Functions In Your Shell

Define these functions in your SSH shell:

```bash
site_status() {
  systemctl --user status site.service
}

site_logs() {
  journalctl --user -u site.service --since "5 minutes ago"
}
```

Call `site_status`, then press `q` to leave the view. Call `site_logs` and leave with `q` too. These functions read state and logs; they do not start or stop Caddy.

## Keep Only If Useful

The definitions disappear when this shell ends. To keep them, save just the definitions in `~/src/scripts/site-functions.sh`, outside published pages. Preserve any existing content:

```bash
mkdir -p ~/src/scripts
micro ~/src/scripts/site-functions.sh
```

`source` runs a file in your current shell, making its definitions available there. Read the file first and source only content you trust. In a fresh SSH shell:

```bash
source ~/src/scripts/site-functions.sh
site_status
```

The service does not depend on these shortcuts. If you keep the file, review and commit it with your other source.

## Explain To A Peer

Explain what happens when you define `site_logs`, when you call it, and when you source the saved file. Why does none of this stop the website? Use `guide answer 'Your explanation'` when this quest is current.

## Related Reading

- [Bash functions](../concepts/bash-functions.md)
- [Watch service logs](watch-service-logs.md)
- [Systemctl](../commands/systemctl.md)
