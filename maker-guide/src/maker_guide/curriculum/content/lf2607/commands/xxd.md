# xxd

## Use

```bash
printf 'A\n' | xxd
```

## What It Does

`xxd` shows bytes in hexadecimal and ASCII columns.

It is useful when a file is not safe or meaningful to print with `cat`.

## Practice

Expect hexadecimal `41 0a`: ASCII `A`, then a newline. Use `xxd -l 32 /bin/ls` to inspect only the first 32 bytes of a Linux executable.

## Watch Out

Hex output is low-level. Pair it with `file` first.

## Docs Pointers

- Run `man xxd`.
- Read [File Encoding](../concepts/file-encoding.md).
- Read [Number Bases: Decimal, Hexadecimal, Octal](../concepts/number-bases.md).
