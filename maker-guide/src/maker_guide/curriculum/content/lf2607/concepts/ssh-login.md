# Concept: SSH Login

SSH lets your terminal talk to a shell running on another machine.

Requires a remote account and host supplied by its administrator. Replace both placeholders:

```bash
ssh username@server.example
```

The example address is not a live server. After connecting, `whoami` identifies the remote account and `hostname` identifies the remote machine. Commands now affect that machine, not your laptop. `exit` closes the remote shell and returns to the local one.

Verify the server's host-key fingerprint before accepting a new key. A changed-key warning needs investigation, not deletion of the warning. Classroom addresses are in [Platform Reference](../guides/platform-reference.md); home Ubuntu practice does not need SSH.

## Go Deeper

- [Terminal](terminal.md) explains the local text interface you use before and during SSH.
- [Shell](shell.md) explains the remote command interpreter you reach after login.
- [Client](client.md) and [Server](server.md) explain why `ssh` is a client contacting an SSH server.
