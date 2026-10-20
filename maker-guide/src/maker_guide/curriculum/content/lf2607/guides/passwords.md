# Passwords and Passphrases

Use a **different password for each account**. A password manager can generate and store strong passwords; for one you must remember, choose several randomly selected, unrelated words.

Do not use an example from a guide as your real password. Length helps, but a familiar quotation, personal detail, or predictable pattern is still guessable.

## Choose a classroom passphrase

The classroom requires **at least 18 characters** and checks for dictionary matches, account details, repeated characters, and simple sequences. It does not require a mixture of uppercase, lowercase, digits, and punctuation.

Aim for four or more unrelated words, long enough to pass the policy. Avoid:

- Your name, username, school, birthday, or project name.
- A common phrase or password with small edits.
- Keyboard patterns, repeated characters, or one word with a number appended.
- A secret already used on another account.

The installed policy makes the final decision; satisfying the length rule alone does not guarantee acceptance. At home, Ubuntu's policy may differ, but uniqueness and unpredictability still matter.

## Change your own password

In the shell of the account you want to change:

```bash
whoami
passwd
```

Read each prompt: usually current password, new password, then confirmation. **Nothing appears while typing**. A rejection means the change was not accepted; read the reason and try a less predictable passphrase. Confirm the success message before leaving.

During classroom SSH, this changes your **classroom account password**, not your laptop password or SSH key passphrase. Changing the account password also does not revoke existing authorized SSH keys.

## If you cannot sign in

Check the username and whether SSH is asking for the account password or a key passphrase. Use classroom browser recovery or contact the instructor if necessary. Do not send anyone the password, private key, or a private recovery link.

For a lost or exposed SSH key, follow [SSH Keys](../concepts/ssh-keys.md#replace-a-lost-or-exposed-key); changing the account password alone is not enough.
