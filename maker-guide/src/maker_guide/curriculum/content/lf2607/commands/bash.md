# bash

## Use

```bash
work=$(mktemp -d)
printf '#!/bin/bash\nprintf "hello\\n"\n' > "$work/hello.sh"
bash "$work/hello.sh"
```

## What It Does

`bash` runs the commands saved in a text file called a script.

## Practice

The example creates a script and prints `hello`. Reveal each command as Bash runs it:

```bash
bash -x "$work/hello.sh"
```

Trace lines begin with `+` and go to stderr. Normal script stdout remains separate.

Tracing can expose expanded secrets; do not share a trace without reviewing it.

## Watch Out

Shell syntax depends on the shell. These scripts use Bash.

## Shebang Connection

`bash script.sh` runs Bash explicitly and needs no extra permissions. Direct execution with `./report.sh` needs execute permission and a shebang such as `#!/bin/bash`.

## Docs Pointers

- Run `man bash`.
- Read [Shebang](../concepts/shebang.md).
- Read [Shell Scripting](../concepts/shell-scripting.md).
