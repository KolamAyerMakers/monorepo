# SSH Keys

An SSH key pair lets your device prove its identity without sending your account password for each login.

- Private key: stays secret on your computer. Never send it anywhere.
- Public key: can be copied to a server.

Before generating or inspecting a key, use a terminal on your own computer, not a remote SSH shell. List `~/.ssh` with `ls -l ~/.ssh` on macOS or Linux, or `Get-ChildItem -Force ~/.ssh` in PowerShell. Inspect filenames without printing private-key contents.

Reuse a safe existing pair: a private key and its matching `.pub` file. Older clients may create `id_rsa` and `id_rsa.pub` with bare `ssh-keygen`, so a missing `id_ed25519.pub` does not prove you need a new key. If only one half of a pair exists, ask for help recovering it rather than overwriting the other half.

Only when a genuinely new pair is needed, select its type explicitly:

```bash
ssh-keygen -t ed25519
```

Accept the default location only if neither of these files already exists:

- `~/.ssh/id_ed25519`: private key.
- `~/.ssh/id_ed25519.pub`: public key.

Otherwise choose an unused filename. Choose a passphrase for the new private key and note both saved paths. At an overwrite prompt, answer `n` or cancel with `Ctrl-C`; never replace an existing key just to match an example.

Use the account and host from your normal SSH login. On macOS or Linux, type `ssh-copy-id -i ~/.ssh/id_ed25519.pub` followed by that `username@host` address, then enter your account password when prompted. Substitute the actual public-key path, such as `~/.ssh/id_rsa.pub`, if you reused another pair or chose a different filename.

In PowerShell on Windows, `Get-Content ~/.ssh/id_ed25519.pub` is a preview-only command: it displays the public key and changes nothing. Substitute your actual `.pub` path here too. Copy that one line, use your normal SSH command to start a password login, then run on the server:

```sh
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cat >> ~/.ssh/authorized_keys
```

`chmod 700 ~/.ssh` means only you can enter or change that directory. Paste the public-key line you inspected locally, press Enter, then press Ctrl-D. Run `chmod 600 ~/.ssh/authorized_keys` so only you can read or change the key list. This appends without replacing existing keys.

After manual installation, run `exit` to return to your own computer. After either installation method, reconnect from your own computer with your normal SSH command and run `whoami`. For a non-default key filename, insert `-i` followed by the matching private-key path immediately after `ssh` in that command. Your device uses the private key locally to prove it matches the public key installed on the server. A key passphrase prompt is not your server account password prompt.

## Related Docs

- [ssh-keygen](../commands/ssh-keygen.md)
- [ssh-copy-id](../commands/ssh-copy-id.md)
- [ssh](../commands/ssh.md)
