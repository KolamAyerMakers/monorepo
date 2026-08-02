# S2 Recap: Files, Editing, Identity

Session: S2

## What Changed

You moved from reading files to making them. Your homepage stopped being a starter page and became your page. You set up SSH-key login early, from your own computer.

The important model is source versus output:

- `~/src/pages/` is source.
- `~/public_html/` is generated output.
- `build-website` rebuilds output from source.

If the output breaks, rebuild it. If the source breaks, slow down and fix the source.

## Commands You Met

- `touch`: create an empty file or update its timestamp.
- `mkdir`: create a directory.
- `rmdir`: remove an empty directory.
- `cp`: copy files.
- `mv`: move or rename files.
- `rm -i`: ask before removing a file.
- `rm`: remove files.
- `chmod`: change permission modes; here it protects SSH key paths.
- `micro`: edit text.
- `echo`: print text.
- `>`: replace a file with command output.
- `>>`: append command output to a file.
- `ssh-keygen`: generate an SSH key pair.
- `ssh-copy-id`: install your public key on the server.
- `Get-Content`: preview a local public key in PowerShell without changing it.
- `ls -l`: inspect ownership, size, permissions, and names.

`rm -rf` recursively forces removal. You learned what it means, but did not run it in S2.

## Mental Model

Paths matter. `~/playground/file.txt` and `~/src/pages/index.md` are not the same file.

Before changing a file, ask:

1. Where am I?
2. What path am I editing?
3. Is this source or output?
4. Can I rebuild or recreate it if I break it?

## Redirection

Use `>` when you mean "replace this file".

Use `>>` when you mean "add to the end of this file".

If you accidentally use `>` twice, the first content is gone. That is not a bot bug. That is what you asked the shell to do.

## SSH Keys

Your SSH key has two parts:

- Private key: stays on your device. Do not share it.
- Public key: can be copied to the server.

You created the private key on your own computer and protected it with a passphrase.

If a private key is lost or copied, create a replacement and remove the old public key from the server. If you cannot log in, ask the instructor for recovery. Never send a private key.

## Live Core

If you attended live and personalized your homepage, you have the core milestone for S2.

- You can copy, rename, move, and remove playground files deliberately.
- You can explain source under `~/src/pages/` versus generated output under `~/public_html/`.
- You can reconnect with your key without entering the account password, run `whoami`, and know why the private key stays private.
- The guide records your successful public-key login automatically.

## Optional Reinforcement

Use the S2 quests for file-operation repetition and guide-checked proof. Run `guide now` for your current session objective. After you complete it, `guide now` shows your current quest. Submit prompted answers with `guide answer 'your answer'`. Run `guide check` after practical work. A passing check records your progress. If stuck, read the quest guide and ask in public help so the answer teaches more than one person.

## Full Autonomy

Use [S2 Self-Study Guide: Files, Editing, Identity](self-study.md) for editor keys, SSH key safety, source/output recovery, and exact proof checks.
