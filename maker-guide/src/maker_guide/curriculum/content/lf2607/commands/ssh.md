# Command: `ssh`

Use `ssh` to log into another machine.

Requires an account on another machine and its SSH address. Replace both placeholders with the account and host given by its administrator:

```bash
ssh username@server.example
```

This is an address pattern, not a live demo server. Classroom addresses are in [Platform Reference](../guides/platform-reference.md); local Ubuntu practice needs no SSH connection.

If the connection succeeds, you get a shell on the server.

Run `whoami` and `hostname` there to confirm the account and machine. `exit` returns you to your local shell. Verify a new host-key fingerprint with the administrator before accepting it; do not bypass a changed-host-key warning.

## Related Concepts

- [Terminal](../concepts/terminal.md): the interface carrying your keystrokes and output.
- [Shell](../concepts/shell.md): the command interpreter you reach after login.
- [SSH Login](../concepts/ssh-login.md): local and remote shells.
