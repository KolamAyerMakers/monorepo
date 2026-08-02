# Script Arguments

## Core Idea

Arguments let one script handle different inputs.

Inside a shell script:

- `$1` is the first argument.
- `$2` is the second argument.
- `$#` is the number of arguments.
- `"$@"` means all arguments, preserving each one separately.

## Practice Alone

Create a scratch script:

```bash
mkdir -p ~/scripts
micro ~/scripts/args.sh
```

```bash
#!/bin/bash
set -euo pipefail

printf 'count=%s\n' "$#"
printf 'first=%s\n' "${1:-missing}"
```

Run it with different inputs:

```bash
bash ~/scripts/args.sh
bash ~/scripts/args.sh makers
bash ~/scripts/args.sh "two words"
```

## Watch Out

- `$1` is empty when no first argument exists unless strict mode turns that into an error.
- Use a guard before relying on required arguments.
- Quote positional parameters: `"$1"`, not `$1`.

## Done When

You can write a script that behaves differently based on its arguments.

## Docs Pointers

- Read [bash](../commands/bash.md), [printf](../commands/printf.md), [quoting](quoting.md), and [shell scripting](shell-scripting.md).
