# git remote

## Use

Run this in a repository such as the [Git card's demo](git.md). A new local-only repository prints nothing because it has no remote yet.

```bash
git remote -v
```

## What It Does

`git remote` manages named repository URLs such as `origin`.

## Practice

Use `git remote add origin 'REPOSITORY_URL'` only after replacing `REPOSITORY_URL` with a real repository URL. Verify with `git remote -v`; adding a remote does not upload anything. To practise without a hosted account, use the local remote in [git clone](git-clone.md).

## Watch Out

Remote names are labels. `origin` is common, not magic.

## Docs Pointers

- Read [git](git.md), [git push](git-push.md), and [Forgejo publishing](../concepts/forgejo-publishing.md).
- Run `git help remote`.
