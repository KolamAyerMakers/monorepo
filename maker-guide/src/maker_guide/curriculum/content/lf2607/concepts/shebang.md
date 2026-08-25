# Shebang

## Core Idea

A shebang is the special first line that tells Linux which program should read and run a script.

## Shape

```bash
#!/bin/bash
```

The first two characters must be `#!`. In this course, `/bin/bash` means Bash should read and run the remaining lines.

## Why It Matters

These two commands are different:

```bash
bash script.sh
./script.sh
```

The first command explicitly starts Bash and gives it the script. The second names the file in the current directory and asks Linux to run it. That direct route needs execute permission and a valid shebang.

## Common Failures

- `Permission denied`: the script is not executable. Run `chmod u+x script.sh` or execute it with `bash script.sh`.
- `bad interpreter: No such file or directory`: the shebang path is wrong or the file has Windows CRLF line endings.
- Script runs under the wrong shell: check the first line and run `head -n 1 script.sh`.
- `#!/usr/bin/env bash`: common on many systems, but this course uses `#!/bin/bash` for predictability.

## CRLF Check

If a script copied from another system behaves strangely:

```bash
head -n 1 script.sh | xxd
```

If the line ends in `0d 0a`, it has Windows CRLF line endings. Recreate the first line in the terminal editor or ask before doing bulk conversion.

## Docs Pointers

- Run `man bash` and search for `INVOCATION`.
- Read [Shell Scripting](shell-scripting.md), [Script Permissions](script-permissions.md), and [File Encoding](file-encoding.md).
