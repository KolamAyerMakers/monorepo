# Command: `ssh-keygen`

Generate an SSH key pair.

```bash
ssh-keygen
```

## Useful Options

- `-f path`: write the private key to `path` and the public key to `path.pub`.
- `-C comment`: add a comment to the public key.
- `-l -f file`: show a key fingerprint.

Without `-f`, Ed25519 keys default to `~/.ssh/id_ed25519` and `~/.ssh/id_ed25519.pub`.

## Common Failures

- `Saving key failed`: make sure the destination directory exists and is writable.
- Overwrite prompt: stop and inspect the existing key before answering.

## Docs Pointers

- Run `man ssh-keygen`.
- Read [OpenSSH ssh-keygen manual](https://man.openbsd.org/ssh-keygen).
- Read [SSH Keys](../concepts/ssh-keys.md) for key safety and installation.
