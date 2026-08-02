# Command: `chmod`

## Use

```bash
chmod u+x script.sh
```

## What It Does

`chmod` changes permission metadata on files and directories.

## Symbolic Modes

```bash
chmod u+x script.sh
chmod go-r private-notes.txt
chmod a+r public.html
```

- `u`: owner.
- `g`: group.
- `o`: other.
- `a`: all.
- `+`: add permission.
- `-`: remove permission.
- `=`: set exactly.

## Executable Scripts

```bash
chmod +x ~/scripts/hello.sh
./scripts/hello.sh Makers
```

`chmod +x` allows direct execution. It does not fix a broken script, a missing shebang, or bad syntax.

## Watch Out

Use `ls -l` before and after `chmod` so you can see exactly what changed. Do not use numeric modes such as `777` unless you can explain every bit.

## Docs Pointers

- Run `man chmod`.
- Read [permissions](../concepts/permissions.md), [script permissions](../concepts/script-permissions.md), [shebang](../concepts/shebang.md), and [number bases](../concepts/number-bases.md).
