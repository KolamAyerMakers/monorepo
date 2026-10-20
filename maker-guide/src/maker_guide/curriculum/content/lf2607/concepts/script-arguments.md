# Script Arguments

## Core Idea

Arguments let one script handle different inputs.

Inside a Bash script, `$1` is the first argument, `$#` is the argument count, and `"$@"` preserves all arguments separately.

## Practice Alone

Create a scratch script:

```bash
work=$(mktemp -d)
micro "$work/title.sh"
```

```bash
#!/bin/bash

if [[ "$#" -ne 1 || -z "$1" ]]; then
  printf 'usage: %s TITLE\n' "$0" >&2
  exit 1
fi
report_title="$1"
printf 'title=%s\n' "$report_title"
```

Run it with different inputs:

```bash
bash "$work/title.sh" "My Maker Report"
bash "$work/title.sh"
```

## Watch Out

- The first run prints the title; the second prints usage and returns nonzero. The guard also rejects an empty title or extra arguments.
- Quote positional parameters: `"$1"`, not `$1`.

Without a guard, a missing `$1` normally expands to empty; with `set -u`, it is an error. `[[ ... || ... ]]` short-circuits, so the example checks the count before reading `$1`.

## Done When

You can give one script a quoted value and use that value as `$1`.

## Docs Pointers

- Read [bash](../commands/bash.md), [printf](../commands/printf.md), [quoting](quoting.md), and [shell scripting](shell-scripting.md).
