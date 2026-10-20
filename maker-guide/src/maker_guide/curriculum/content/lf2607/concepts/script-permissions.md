# Script Permissions

## Core Idea

Executable permission lets the system run a script directly.

## Practice Alone

Create a fresh script, run it through Bash, then try direct execution:

```bash
work=$(mktemp -d)
printf '#!/bin/bash\nwhoami\n' > "$work/report.sh"
bash "$work/report.sh"
"$work/report.sh"
```

The first run prints your username. The second should fail with `Permission denied`: a newly created ordinary file has no execute bit. Now inspect and change just the owner's execute permission:

```bash
ls -l "$work/report.sh"
chmod u+x "$work/report.sh"
"$work/report.sh"
```

Expect the username again. From that script's directory, `./report.sh` is another path to the same file.

## Done When

You can explain what `./` means, why the owning user's permission triplet needs `x`, and what the shebang tells Linux.

## Go Deeper

- [Shebang](shebang.md) explains what direct execution reads from the first line.
- [Permissions](permissions.md) explains executable bits.
- [Number Bases: Decimal, Hexadecimal, Octal](number-bases.md) explains numeric modes such as `755`.
