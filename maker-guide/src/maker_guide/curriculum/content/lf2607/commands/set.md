# set

## Use

```bash
set -euo pipefail
```

## What It Does

`set` changes shell options for the current shell or script. These options depend on exit status: `0` means success, nonzero means failure.

## Course Options

Stop when a command fails:

```bash
set -e
```

Reject unset variables:

```bash
set -u
```

Make a pipeline fail if any stage fails:

```bash
set -o pipefail
```

Combine them:

```bash
set -euo pipefail
```

## Why Use It

These options make script bugs loud. Without them, a script may continue after an earlier command failed.

## Watch Out

`set -u` makes `$1` fail when no argument was passed. Add argument checks before using positional arguments.

`set -e` is not a replacement for understanding failures. It reacts to nonzero exit statuses; you still need to know which command failed and why.

## Docs Pointers

- Run `help set`.
- Read [shell scripting](../concepts/shell-scripting.md), [script arguments](../concepts/script-arguments.md), [pipes](../concepts/pipes.md), and [exit](exit.md).
