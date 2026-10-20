# fj

## Use

Requires the Forgejo CLI `fj` and authentication configured for a Forgejo server you may use. No Forgejo account is required for local Git practice. Classroom setup is described in [Platform Reference](../guides/platform-reference.md).

```bash
fj repo create practice-notes
```

## What It Does

`fj` creates and manages Forgejo repositories from the terminal. This command creates an empty remote repository; it does not initialize your local directory or upload files.

## Practice

Choose an unused repository name, create it once, then use the URL shown by Forgejo with [git remote](git-remote.md). Push only after checking the destination and your staged/committed contents.

## Watch Out

Do not put tokens in commands, chat, or source files. If the repository already exists, inspect it instead of trying to create it again.

## Docs Pointers

- Read [Forgejo publishing](../concepts/forgejo-publishing.md) and [git remote](git-remote.md).
