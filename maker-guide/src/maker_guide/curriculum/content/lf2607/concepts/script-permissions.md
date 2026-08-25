# Script Permissions

## Core Idea

Executable permission lets the system run a script directly.

## Practice Alone

Create a script named `report.sh` in `~/scripts`: its first line is `#!/bin/bash`, followed by one ordinary command such as `whoami`. From `~/scripts`, run `bash report.sh`, then try `./report.sh` and observe `Permission denied`. Inspect with `ls -l`, add `chmod u+x report.sh`, and run `./report.sh` again.

## Done When

You can explain what `./` means, why the owning user's permission triplet needs `x`, and what the shebang tells Linux.

## Go Deeper

- [Shebang](shebang.md) explains what direct execution reads from the first line.
- [Permissions](permissions.md) explains executable bits.
- [Number Bases: Decimal, Hexadecimal, Octal](number-bases.md) explains numeric modes such as `755`.
