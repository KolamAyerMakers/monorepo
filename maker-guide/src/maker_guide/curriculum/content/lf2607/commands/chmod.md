# Command: `chmod`

## Use

```bash
work=$(mktemp -d)
printf '#!/bin/bash\nprintf "hello\\n"\n' > "$work/script.sh"
ls -l "$work/script.sh"
chmod u+x "$work/script.sh"
"$work/script.sh"
```

## What It Does

`chmod` changes permission metadata on files and directories.

## Symbolic Modes

```bash
chmod u+x "$work/script.sh"
chmod go-r "$work/script.sh"
chmod a+r "$work/script.sh"
```

- `u`: user who owns the file.
- `g`: group.
- `o`: other.
- `a`: all.
- `+`: add permission.
- `-`: remove permission.
- `=`: set exactly.

## Executable Scripts

`chmod u+x` adds execute permission for the user who owns the file. It does not fix a broken script, a missing shebang, or bad syntax.

## Watch Out

Use `ls -l` before and after `chmod` so you can see exactly what changed. Do not use numeric modes such as `777` unless you can explain every bit.

## Docs Pointers

- Run `man chmod`.
- Read [permissions](../concepts/permissions.md), [script permissions](../concepts/script-permissions.md), [shebang](../concepts/shebang.md), and [number bases](../concepts/number-bases.md).
