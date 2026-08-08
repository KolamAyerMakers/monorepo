# Ignore scratch files

Quest: ignore-scratch-files

## Mission

Preserve the starter ignore rules, add `*.tmp`, then prove the scratch file stays out of Git status.

## Why This Matters

Git ignore rules only affect files inside the repository. `~/public_html/` is already outside the `~/src` repository, so it does not need a `public_html/` ignore rule there. Ignore rules are for disposable files that actually appear inside source.

## Commands You Will Use

- `micro`
- `touch`
- `git status`

## Steps

1. Add the line `*.tmp` to `~/src/.gitignore` without removing its existing rules.
2. You can use an editor or run `echo '*.tmp' >> ~/src/.gitignore`.
3. Run `cd ~/src`.
4. Run `touch scratch.tmp`.
5. Run `git status`. The optional `--short` flag only makes the output compact.
6. Confirm `scratch.tmp` is not listed.
7. Run `guide check`.

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
