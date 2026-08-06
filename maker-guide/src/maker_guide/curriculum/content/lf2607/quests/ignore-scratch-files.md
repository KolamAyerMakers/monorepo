# Ignore scratch files

Quest: ignore-scratch-files

## Mission

Preserve the starter ignore rules, add `*.tmp`, then prove git status stays clean.

## Why This Matters

Git ignore rules only affect files inside the repository. `~/public_html/` is already outside the `~/src` repository, so it does not need a `public_html/` ignore rule there. Ignore rules are for disposable files that actually appear inside source.

## Commands You Will Use

- `micro`
- `touch`
- `git status`

## Steps

1. Open `micro ~/src/.gitignore`.
2. Keep the existing `node_modules/` and `dist/` rules.
3. Add the line `*.tmp`.
4. Save the file.
5. Run `cd ~/src`.
6. Run `touch scratch.tmp`.
7. Run `git status --short`.
8. Confirm `scratch.tmp` is not listed.
9. Ask the guide to check `.gitignore`.

## Hints

1. `.gitignore` lives at the repository root.
2. The starter rules must remain.
3. The new line must be `*.tmp`.

## If Check Fails

Make sure the file is named `.gitignore` and contains `node_modules/`, `dist/`, and `*.tmp` on their own lines.

## Related Reading

- [git status](../commands/git-status.md)
- [touch](../commands/touch.md)
- [glob patterns](../concepts/glob-pattern.md)
- [git-basics](../concepts/git-basics.md)
