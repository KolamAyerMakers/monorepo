# Ignore scratch files

Quest: ignore-scratch-files

## Mission

Create `~/src/.gitignore` that ignores `*.tmp`, then prove git status stays clean.

## Why This Matters

Git ignore rules only affect files inside the repository. `~/public_html/` is already outside the `~/src` repository, so it does not need a `public_html/` ignore rule there. Ignore rules are for disposable files that actually appear inside source.

## Commands You Will Use

- `micro`
- `touch`
- `git status`

## Steps

1. Open `micro ~/src/.gitignore`.
2. Add the line `*.tmp`.
3. Save the file.
4. Run `touch ~/src/scratch.tmp`.
5. Run `git status --short` from `~/src`.
6. Confirm `scratch.tmp` is not listed.
7. Ask the guide to check `.gitignore`.

## Hints

1. `.gitignore` lives at the repository root.
2. One line is enough for this quest.
3. The line must be `*.tmp`.

## If Check Fails

Make sure the file is named `.gitignore` and contains `*.tmp` on its own line.

## Related Reading

- [git status](../commands/git-status.md)
- [touch](../commands/touch.md)
- [git-basics](../concepts/git-basics.md)
