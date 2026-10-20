# Command: `ssh-copy-id`

Install your public SSH key on the server.

Requires a matching key pair on your own computer and a remote account you can already log into. Replace the example account, host, and public-key filename with your actual values:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub username@server.example
```

Run this on your own Ubuntu machine, not in the remote shell. See [SSH Keys](../concepts/ssh-keys.md) before creating or replacing a key.

## What It Does

`ssh-copy-id` appends your public key to the remote account's `~/.ssh/authorized_keys`. After that, SSH can prove your identity with the private key instead of only a password.

## Expected Flow

1. It connects to the server.
2. It may ask for your account password one last time.
3. It installs the public key.
4. You disconnect, reconnect with that same personal SSH address, and run `whoami`.

## Common Failures

- Wrong account: verify the username and host from your normal login, not a registration account.
- `No identities found`: reuse a safe existing key or generate one with `ssh-keygen` only when needed.
- Permission denied: check username and password, then confirm the account exists.
- Still asks for password after install: use verbose mode with your personal SSH address and inspect which key files SSH tries.

## Docs Pointers

- Run `man ssh-copy-id`.
- Read [SSH Keys](../concepts/ssh-keys.md).
