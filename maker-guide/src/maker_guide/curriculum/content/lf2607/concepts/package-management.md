# Package Management

## Core Idea

A package manager keeps track of installable software, versions, dependencies, files, and updates. On Debian-family systems, `apt` is the user-facing package tool and `dpkg` is the lower-level package database tool.

## Discovery Versus Installation

```bash
apt search ascii
apt show cmatrix
```

Searching and showing package metadata are safe learner actions. Installing packages changes the shared machine and is an administrator action in this course.

## What `apt show` Tells You

- Package name and version.
- Repository source.
- Dependencies.
- Installed size.
- Human description.

Read the description before deciding whether a package is relevant. Do not infer purpose from the name alone.

## Common Confusions

- `apt search` searches package names and descriptions, not your files.
- `sudo apt install` is not appropriate on a shared class server unless an administrator asks you to run it.
- Package availability depends on configured repositories and operating system release.
- A command can exist without the package having the same name.

## Proof Check

Use `apt show cmatrix` and explain what it does without installing it.

## Docs Pointers

- Run `man apt`, then read `search` and `show`.
- Run `man apt-cache` for older but still common package query examples.
- Read [Debian package management basics](https://www.debian.org/doc/manuals/debian-handbook/sect.apt-cache.en.html).
