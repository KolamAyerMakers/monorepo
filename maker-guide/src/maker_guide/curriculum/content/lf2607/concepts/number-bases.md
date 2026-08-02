# Number Bases: Decimal, Hexadecimal, Octal

## Core Idea

Computers store bits. Humans write numbers in different bases to make those bits readable. Decimal is base 10. Hexadecimal is base 16. Octal is base 8.

## Why Linux Uses These Bases

- Decimal: normal counts, sizes, process ids, ports.
- Hexadecimal: byte inspection, memory, colors, hashes, binary file views.
- Octal: Unix permission shorthand such as `755` and `644`.

## Commands To Try

```bash
printf 'A' | xxd
printf '%d\n' 0x41
stat -c '%a %n' ~/playground 2>/dev/null || true
```

`0x41` is hexadecimal for decimal `65`, which is the ASCII byte for `A`. Permission mode `755` is octal: owner can read, write, execute; group and others can read and execute.

## Permission Octal

```text
read    = 4
write   = 2
execute = 1
```

Add them per permission triplet:

```text
7 = 4 + 2 + 1 = rwx
6 = 4 + 2     = rw-
5 = 4     + 1 = r-x
4 = 4         = r--
```

## Common Confusions

- `10` means different values in different bases: decimal ten, binary two, octal eight, hexadecimal sixteen.
- Hex digits continue after `9` with `a` through `f`.
- Octal permissions are compact, but symbolic modes such as `u+x` are often safer while learning.

## Proof Check

Explain why `chmod 755 script.sh` gives the owner write permission but `chmod 555 script.sh` does not.

## Docs Pointers

- Run `man chmod`, then read numeric mode descriptions.
- Run `man xxd`.
- Read [Wikipedia on hexadecimal](https://en.wikipedia.org/wiki/Hexadecimal) and [Wikipedia on octal](https://en.wikipedia.org/wiki/Octal).
