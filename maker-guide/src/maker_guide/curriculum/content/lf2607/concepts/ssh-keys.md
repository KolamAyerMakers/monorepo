# SSH Keys

An SSH key pair lets your device prove its identity without sending your account password for each login.

- Private key: stays secret on your computer. Never send it anywhere.
- Public key: can be copied to a server.

Before generating a key, read your prompt. A prompt ending in `@lf2607` means you are on the server. Run `exit`, then use a terminal on your own computer.

```bash
ssh-keygen
```

Only create a key when `~/.ssh/id_ed25519.pub` does not already exist or its private key is no longer safe. Accept the defaults to create:

- `~/.ssh/id_ed25519`: private key.
- `~/.ssh/id_ed25519.pub`: public key.

Choose a passphrase for a newly created private key. Reuse a safe existing key rather than creating another one for this course.

On macOS or Linux, type `ssh-copy-id ` followed by the address from your personal registration command, then enter your password when prompted. In Windows Terminal or PowerShell, `Get-Content ~/.ssh/id_ed25519.pub` is a preview-only command: it displays the public key and changes nothing. Copy that one line, use the same personal command to start a password SSH session, then run:

```sh
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cat >> ~/.ssh/authorized_keys
```

`chmod 700 ~/.ssh` means only you can enter or change that directory. Paste the one line printed locally by `Get-Content ~/.ssh/id_ed25519.pub`, press Enter, then press Ctrl-D. Run `chmod 600 ~/.ssh/authorized_keys` so only you can read or change the key list, then `exit`, reconnect with the same personal command, and run `whoami`. This appends the key without replacing existing recovery keys. Your device uses the private key to prove it has the matching public key installed on the server.

## Related Docs

- [ssh-keygen](../commands/ssh-keygen.md)
- [ssh-copy-id](../commands/ssh-copy-id.md)
- [ssh](../commands/ssh.md)
