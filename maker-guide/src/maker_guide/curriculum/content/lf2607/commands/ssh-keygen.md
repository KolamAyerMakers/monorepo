# Command: `ssh-keygen`

Generate an SSH key pair.

Use a terminal on your own computer, not a remote SSH shell. First inspect `~/.ssh` with `ls -l ~/.ssh` on macOS or Linux, or `Get-ChildItem -Force ~/.ssh` in PowerShell. Reuse a safe existing private/public pair, including an `id_rsa` pair; a missing `id_ed25519.pub` does not mean you have no key. Do not display private-key contents.

Only generate a genuinely new pair when needed, using filenames that do not already exist:

```bash
ssh-keygen -t ed25519
```

Choose a passphrase. Accept the default location only if neither the private-key path nor its `.pub` path exists. Otherwise choose an unused filename. Never overwrite an existing key; cancel an overwrite prompt with `n` or `Ctrl-C`.

## Useful Options

- `-t ed25519`: explicitly select Ed25519 instead of relying on the client's default key type.
- `-f path`: write the private key to `path` and the public key to `path.pub`.
- `-C comment`: add a comment to the public key.
- `-l -f file`: show a key fingerprint.

With `-t ed25519` and no `-f`, the default paths are `~/.ssh/id_ed25519` and `~/.ssh/id_ed25519.pub`. Keep the saved paths: installation must use the actual `.pub` file, not an assumed filename. See [SSH Keys](../concepts/ssh-keys.md) for installation.

## Common Failures

- `Saving key failed`: make sure the destination directory exists and is writable.
- `id_ed25519.pub` is missing: older clients may have created `id_rsa.pub` when run without `-t`. Inspect and reuse the actual safe pair. If only the private key remains, ask for help recovering its public key rather than replacing it.
- Overwrite prompt: answer `n` or cancel, then inspect the existing filenames.

## Docs Pointers

- Run `man ssh-keygen`.
- Read [OpenSSH ssh-keygen manual](https://man.openbsd.org/ssh-keygen).
- Read [SSH Keys](../concepts/ssh-keys.md) for key safety and installation.
