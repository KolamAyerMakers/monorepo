# set

## Use

```bash
set -u
```

## What It Does

`set` changes shell options for the current shell or script. Different options react to different problems.

## Course Options

Reject expansion of an unset variable or positional parameter:

```bash
set -u
```

In a simple straight-line script, exit after an unhandled command returns nonzero:

```bash
set -e
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

These options can make script bugs loud. Without `-u`, a missing value can silently become empty. Without deliberate failure handling, a script can continue after an earlier command failed.

## Watch Out

`set -u` makes `$1` fail when no argument was passed. It does not reject a supplied empty argument. Add argument checks before using positional arguments.

`set -e` is not a universal "stop on every error" rule. It has exceptions in conditions, `&&` and `||` lists, negation, and pipelines. It is not a replacement for understanding which command failed or handling expected failures explicitly.

`set -e` alone does not make every pipeline fail when an earlier stage fails. `pipefail` changes that behavior and should be learned separately.

## Docs Pointers

- Run `help set`.
- Read [shell scripting](../concepts/shell-scripting.md), [script arguments](../concepts/script-arguments.md), [pipes](../concepts/pipes.md), and [exit](exit.md).
