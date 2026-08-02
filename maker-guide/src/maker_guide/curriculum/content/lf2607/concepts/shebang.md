# Shebang

## Core Idea

A shebang is the first line of an executable script that tells the kernel which interpreter should run the file.

## Shape

```bash
#!/bin/bash
```

The first two characters must be `#!`. The path after them must point to an interpreter. In this course, Bash scripts use `/bin/bash`.

## Why It Matters

These two commands are different:

```bash
bash ~/scripts/hello.sh Makers
~/scripts/hello.sh Makers
```

The first command explicitly runs Bash and gives it the script. The second asks the system to execute the file directly. Direct execution needs executable permission and a valid shebang so the system knows which interpreter to start.

## Safe Script Header

```bash
#!/bin/bash
set -euo pipefail
```

Use this at the top of course Bash scripts unless a quest says otherwise.

## Common Failures

- `Permission denied`: the script is not executable. Run `chmod +x script.sh` or execute it with `bash script.sh`.
- `bad interpreter: No such file or directory`: the shebang path is wrong or the file has Windows CRLF line endings.
- Script runs under the wrong shell: check the first line and run `head -n 1 script.sh`.
- `#!/usr/bin/env bash`: common on many systems, but this course uses `#!/bin/bash` for predictability.

## CRLF Check

If a script copied from another system behaves strangely:

```bash
head -n 1 script.sh | xxd
```

If the line ends in `0d 0a`, it has Windows CRLF line endings. Recreate the first line in the terminal editor or ask before doing bulk conversion.

## Proof Check

Create a tiny script with `#!/bin/bash`, add `chmod +x`, run it directly, then run the same script with `bash script.sh`. Explain which command used the shebang.

## Docs Pointers

- Run `man bash` and search for `INVOCATION`.
- Run `man 2 execve`.
- Read [Shell Scripting](shell-scripting.md), [Script Permissions](script-permissions.md), and [File Encoding](file-encoding.md).
