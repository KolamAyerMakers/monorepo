# S2 — Files, Editing, Identity

Create, edit, move, and remove practice files. Then learn how an SSH key identifies you.

**You need:** your classroom shell or the Ubuntu setup in [Continue at Home](../../guides/continue-at-home.md). All file exercises run there. SSH key setup runs on **your own computer**, except where labelled.

## 1. Make a playground

Use these filenames only for practice. If they already contain work you want to keep, use a new practice directory instead.

```bash
mkdir -p ~/playground
cd ~/playground
touch one.txt two.txt three.txt
micro micro-note.txt
```

Type `edited with micro`. Save with `Ctrl-S`; quit with `Ctrl-Q`.

```bash
cat micro-note.txt
ls -l
```

Check the saved text. In `ls -l`, find your username in the owner column. `touch` creates a missing file; it does not erase an existing file.

## 2. Replace or append

Predict the final contents before running:

```bash
echo "hello makers" > hi.txt
echo again >> hi.txt
cat hi.txt
echo "first version" > overwrite-demo.txt
echo replacement > overwrite-demo.txt
cat overwrite-demo.txt
```

`hi.txt` has two lines. `overwrite-demo.txt` has only `replacement`.

**`>` replaces; `>>` appends.** The shell performs the redirection, so check the destination before pressing Enter.

## 3. Copy, move, remove

```bash
cp one.txt one-copy.txt
mv one-copy.txt one-renamed.txt
mkdir moved
mv one-renamed.txt moved/
ls -l moved
rm -i moved/one-renamed.txt
rmdir moved
mkdir empty-directory
rmdir empty-directory
```

Answer `y` to the removal prompt only after checking its path.

- `cp` copies; `mv` moves or renames. Both can replace an existing destination; use `-i` when unsure.
- `rm -i` asks before removing. Shell deletion normally has no trash or undo.
- `rmdir` removes an empty directory, refusing one that still contains entries.

## 4. Edit source, not output

Your site's Markdown is in `~/src/pages`. Generated HTML is in `~/public_html`.

```bash
micro ~/src/pages/index.md
```

Replace the starter heading with your own and save. **In class**, run `build-website` and reload your static homepage. **At home**, run `cd ~/src && node scripts/build.mjs` and use your local preview.

Find your new heading in the browser. A source edit is not published until a successful build. Editing generated HTML is temporary: the next build replaces it.

## 5. Set up an SSH key — optional at home

A key pair has a **private key**, which stays on your computer, and a **public key**, which the server stores. A passphrase protects the private-key file. It is not your server account password.

At home, skip this section unless you have another machine or Git host to connect to. A local shell needs no SSH key.

### A. Inspect on your own computer

If still in classroom SSH, run `exit` first. Check existing filenames without printing private-key contents:

```bash
ls -l ~/.ssh
```

In Windows PowerShell, use `Get-ChildItem -Force ~/.ssh` instead. A missing directory is normal for a first key.

Look for a pair such as `id_ed25519` / `id_ed25519.pub` or `id_rsa` / `id_rsa.pub`. Reuse your own pair if its private key has not been exposed. A missing `.pub` file is **not** a reason to overwrite its private key; get help recovering the public key if needed.

For a new pair:

```bash
ssh-keygen -t ed25519
```

Choose a passphrase. Accept the default filename only if neither file exists. Otherwise choose an unused filename. At an overwrite prompt, answer `n` or cancel with `Ctrl-C`.

### B. Install the public key

**Linux/macOS, on your computer:**

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub username@lf2607.kolamayermakers.org
```

Use your actual username and public-key path.

**Windows PowerShell, on your computer:**

```powershell
Get-Content ~/.ssh/id_ed25519.pub
```

Copy that public-key line. Sign into the classroom using your password. **In the classroom shell:**

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
cat >> ~/.ssh/authorized_keys
```

Paste the line, press Enter, then `Ctrl-D` on the empty line. This appends rather than replacing existing keys.

```bash
chmod 600 ~/.ssh/authorized_keys
exit
```

### C. Test from your own computer

Reconnect with your personal SSH command and run `whoami`. You should not need the **account password**; a **key passphrase** prompt is normal.

For a non-default filename, select the private key explicitly:

```bash
ssh -i ~/.ssh/my-class-key username@lf2607.kolamayermakers.org
```

If it fails, use `ssh -v` with the same command to see which key was offered; do not publish the whole log without reviewing it. Keep password/browser access until the key works.

If a private key is lost or exposed, test a replacement first, then remove its old public-key line from `authorized_keys`. Never send anyone the private key.

## Check yourself

- Your playground contains the three empty files, the editor note, and the two redirection examples.
- The practice `moved` directory is gone; your original `one.txt` remains.
- Your source edit appears in the rebuilt site.
- Can you explain which key may be copied and why an existing key must not be overwritten?

[Answers](../../guides/self-study-answers.md#s2-files-and-keys). References: [micro](../../commands/micro.md), [Redirection](../../commands/redirect.md), and [SSH Keys](../../concepts/ssh-keys.md).
