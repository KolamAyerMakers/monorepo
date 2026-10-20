# Glob Patterns

## Core Idea

A glob pattern matches path names. Git reads `.gitignore` patterns to decide which untracked paths to hide from `git status`.

## Ignore Patterns

| Pattern | Matches |
|---|---|
| `*.tmp` | Any path ending in `.tmp`, such as `scratch.tmp`. |
| `node_modules/` | Directories named `node_modules`. |
| `dist/` | Directories named `dist`. |

`*` means any amount of filename text. A trailing `/` means a directory.

## Repository Scope

Patterns in a repository's `.gitignore` apply within that repository, not to sibling directories.

An ignored untracked file stays untracked. A pattern does not remove a file from Git history or hide a file that Git already tracks.

## Related Ideas

Shell globs and `.gitignore` patterns are related, but the shell evaluates patterns in commands while Git evaluates `.gitignore` patterns.

## Done When

You can explain why `*.tmp` hides `scratch.tmp` from `git status`.

## Docs Pointers

- Run `man gitignore`.
- Read [Git Basics](git-basics.md) and [Quoting](quoting.md).
