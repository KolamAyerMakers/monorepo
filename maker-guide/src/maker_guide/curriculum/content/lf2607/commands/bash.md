# bash

## Use

```bash
bash script.sh
```

## What It Does

`bash` runs the commands saved in a text file called a script.

## Practice

Save commands one per line in a file such as `~/scripts/report.sh`, then run it:

```bash
cd ~/scripts
bash report.sh
```

Reveal each command as Bash runs it:

```bash
bash -x report.sh
```

Trace lines begin with `+` and go to stderr. Normal script stdout remains separate.

## Watch Out

Shell syntax depends on the shell. These scripts use Bash.

## Shebang Connection

`bash script.sh` runs Bash explicitly and needs no extra permissions. Direct execution with `./report.sh` needs execute permission and a shebang such as `#!/bin/bash`.

## Docs Pointers

- Run `man bash`.
- Read [Shebang](../concepts/shebang.md).
- Read [Shell Scripting](../concepts/shell-scripting.md).
