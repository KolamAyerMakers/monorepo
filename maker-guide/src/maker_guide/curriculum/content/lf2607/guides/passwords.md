# Passwords

Use a passphrase: a few memorable words or a short sentence that only makes sense to you.

Do not use any example from this document as your real password. The examples show the shape of a good passphrase, not a secret to reuse.

Good patterns:

- `three unrelated words plus a private detail`
- `a short sentence with one odd memory`
- `place object action detail`

Bad patterns:

- your username, name, nickname, school, or project name
- common passwords with small edits
- keyboard walks like `qwerty` or `asdf`
- one dictionary word with numbers on the end
- anything copied from a document, chat message, or web page

The server checks new passwords with the system password-quality policy. It rejects short passwords, common words, dictionary matches, repeated patterns, and passwords derived from your account details.

Change your password with the normal Linux command:

```bash
passwd
```

If `passwd` rejects your choice, read the message and make the passphrase longer or less predictable. Adding one more unrelated word is usually better than adding punctuation.

Admin password helper scripts still exist for account recovery, but students should use `passwd` for ordinary password changes.
