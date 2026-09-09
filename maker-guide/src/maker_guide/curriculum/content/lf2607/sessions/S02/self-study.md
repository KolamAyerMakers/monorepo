# S2 Self-Study Guide: Files, Editing, Identity

Session: S2

## Study Path

1. Inspect local SSH keys; reuse a safe pair or create a new one with a passphrase, install its public key, and reconnect without your account password.
2. Create a safe workspace under `~/playground/`.
3. Create files with `touch`, use `micro` to write the exact note `edited with micro`, and verify with `cat`.
4. Practice `>`, `>>`, `cp`, `mv`, `rm -i`, and `rmdir` only in the playground first.
5. Edit `~/src/pages/index.md`, run `build-website` successfully, then refresh `https://lf2607.kolamayermakers.org/~username/`.
6. Run `guide now` for your current session objective. After you complete it, `guide now` shows your current quest. Submit prompted answers with `guide answer 'your answer'`. Run `guide check` after practical work.

## Mental Model

Files are named byte containers. Directories map names to files and subdirectories. Your website source is Markdown under `~/src/pages/`; generated HTML is output under `~/public_html/`. If output breaks, rebuild from source. If source breaks, edit source carefully and commit it later.

## Exact Editor Keys

- Open: `micro path/to/file`
- Save: `Ctrl-S`
- Quit: `Ctrl-Q`
- If you edited the wrong file, save nothing important, quit, run `pwd`, and reopen the correct path.

## Redirection Checks

```bash
cd ~/playground
echo "hello makers" > hi.txt
cat hi.txt
echo again >> hi.txt
cat hi.txt
echo "first version" > overwrite-demo.txt
cat overwrite-demo.txt
echo replacement > overwrite-demo.txt
cat overwrite-demo.txt
```

Expected final contents:

```text
hi.txt:
hello makers
again

overwrite-demo.txt:
replacement
```

`>` replaces a file. `>>` appends. This distinction matters because replacing source accidentally loses work.

## Move And Remove Safely

```bash
cp ~/playground/one.txt ~/playground/one-copy.txt
mv ~/playground/one-copy.txt ~/playground/one-renamed.txt
mkdir ~/playground/moved
mv ~/playground/one-renamed.txt ~/playground/moved/
mkdir ~/playground/empty-directory
rmdir ~/playground/empty-directory
rm -i ~/playground/moved/one-renamed.txt
rmdir ~/playground/moved
ls -l ~/playground
```

`mv` moves or renames. `rm -i` asks before removing a file. `rmdir` removes empty directories and refuses non-empty ones. `rm -rf` recursively forces removal, so do not run it in S2. There is no trash where you can recover files. Make mistakes in the playground, not in source.

## SSH Key Safety

Before generating or inspecting a key, read your prompt. A prompt ending in `@lf2607` means you are on the server. Run `exit`, then use a terminal on your own computer.

Inspect `~/.ssh` with `ls -l ~/.ssh` on macOS or Linux, or `Get-ChildItem -Force ~/.ssh` in PowerShell. A missing directory means there are no keys at that location. Look for a private key and its matching `.pub` file, such as `id_ed25519` and `id_ed25519.pub`, or `id_rsa` and `id_rsa.pub`. List filenames, not private-key contents. Reuse a safe existing pair.

A previous bare `ssh-keygen` on an older client may have created `id_rsa`, not `id_ed25519`. If `id_ed25519.pub` is missing but your safe `id_rsa` pair exists, use `~/.ssh/id_rsa.pub` below instead. A missing public-key file alone is not a reason to replace its private key. If you find only half a pair or are unsure which key is safe, ask the instructor.

Only for a genuinely new pair, run `ssh-keygen -t ed25519` and choose a passphrase. Accept the default location only when neither `~/.ssh/id_ed25519` nor `~/.ssh/id_ed25519.pub` exists; otherwise choose an unused filename. At any overwrite prompt, answer `n` or cancel with `Ctrl-C`. Note the saved paths. The private key stays on your own computer; only the `.pub` file is safe to install on the server.

On macOS or Linux, type `ssh-copy-id -i ~/.ssh/id_ed25519.pub` followed by the address from your personal registration command. Replace the example `.pub` path with the actual public-key path you selected. Reconnect using your personal command without entering your account password and run `whoami`.

In PowerShell on Windows, run `Get-Content ~/.ssh/id_ed25519.pub`, substituting your actual `.pub` path. This preview-only command displays the public key and changes nothing. Copy that one public-key line, then use your personal registration command to sign in with your password. On the server, run `mkdir -p ~/.ssh`, then `chmod 700 ~/.ssh` so only you can enter or change that directory. Run `cat >> ~/.ssh/authorized_keys`; paste the line, press Enter and Ctrl-D, then run `chmod 600 ~/.ssh/authorized_keys` so only you can read or change the key list. This appends without replacing existing keys. Exit, reconnect with the same personal command without entering your account password, and run `whoami`. The guide records a successful public-key login automatically.

If you chose a non-default key filename, insert `-i` followed by its matching private-key path immediately after `ssh` in your personal command so SSH knows which key to use. A key passphrase prompt is different from your server account password prompt.

If your private key is lost or copied, create and test a replacement key, then remove the former public-key line from `~/.ssh/authorized_keys`. If you cannot still log in with another key, use browser SSH recovery or ask the instructor. Never send a private key.

## Troubleshooting

- `No such file or directory`: run `pwd` and `ls` on the parent directory.
- `Permission denied` when running a script: run `ls -l` and ask for help. Permissions are covered in S4.
- `ssh-copy-id` targets `new@...`: wrong target. Use the personal SSH address printed during registration.
- Public page did not change: edit `~/src/pages/index.md`, run `build-website`, then refresh `https://lf2607.kolamayermakers.org/~username/`.

## Proof Checklist

- `~/playground/one.txt`, `two.txt`, and `three.txt` exist; the empty directory and `moved/` were removed deliberately.
- `~/playground/micro-note.txt` contains the exact note.
- `~/playground/hi.txt` contains `hello makers` then `again`.
- You can identify the owner column from `ls -l`.
- You can reconnect with your key without entering the account password, run `whoami`, and explain where the private key stays.
- You made a real edit to `~/src/pages/index.md` and the generated homepage no longer contains `A Linux site under construction` after rebuilding.

## Docs Pointers

- Run `man ssh-keygen`, then search for `ed25519`.
- Run `tldr micro` and `tldr ssh-copy-id`.
- Read [Platform Reference](../../guides/platform-reference.md) for the current host names.
