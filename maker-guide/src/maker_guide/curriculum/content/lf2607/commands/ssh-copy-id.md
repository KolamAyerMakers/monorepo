# Command: `ssh-copy-id`

Install your public SSH key on the server.

Use `ssh-copy-id` followed by the personal SSH address printed during registration. Do not target `new`.

## What It Does

`ssh-copy-id` appends your public key to the remote account's `~/.ssh/authorized_keys`. After that, SSH can prove your identity with the private key instead of only a password.

## Expected Flow

1. It connects to the server.
2. It may ask for your account password one last time.
3. It installs the public key.
4. You disconnect, reconnect with that same personal SSH address, and run `whoami`.

## Common Failures

- Target is `new@...`: wrong account. Use the personal SSH address printed during registration.
- `No identities found`: reuse a safe existing key or generate one with `ssh-keygen` only when needed.
- Permission denied: check username and password, then confirm the account exists.
- Still asks for password after install: use verbose mode with your personal SSH address and inspect which key files SSH tries.

## Docs Pointers

- Run `man ssh-copy-id`.
- Read [SSH Keys](../concepts/ssh-keys.md).
