# Script Arguments

## Core Idea

Arguments let one script handle different inputs.

Inside a shell script:

- `$1` is the first argument.

## Practice Alone

Create a scratch script:

```bash
mkdir -p ~/scripts
micro ~/scripts/title.sh
```

```bash
#!/bin/bash

report_title="$1"
printf 'title=%s\n' "$report_title"
```

Run it with different inputs:

```bash
bash ~/scripts/title.sh "My Maker Report"
```

## Watch Out

- `$1` is empty when no first argument exists. Pass one required title when running the script.
- Quote positional parameters: `"$1"`, not `$1`.

`$2`, `$#`, `"$@"`, and missing-argument guards become useful when later scripts accept more inputs or make decisions.

## Done When

You can give one script a quoted value and use that value as `$1`.

## Docs Pointers

- Read [bash](../commands/bash.md), [printf](../commands/printf.md), [quoting](quoting.md), and [shell scripting](shell-scripting.md).
