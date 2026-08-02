# strings

## Use

```bash
strings /bin/ls | less
```

## What It Does

`strings` extracts readable byte sequences from binary-looking files.

## Real Examples

Inspect a system binary safely:

```bash
strings /bin/ls | less
```

Search for URLs or paths inside a binary:

```bash
strings /usr/bin/curl | grep -i http | head
```

Compare with exact bytes:

```bash
xxd /bin/ls | head
```

## Watch Out

`strings` ignores file structure. A readable word inside a binary is evidence, not proof of meaning.

## Docs Pointers

- Run `man strings`.
- Read [file encoding](../concepts/file-encoding.md), [file](file.md), [xxd](xxd.md), and [regular expressions](../concepts/regular-expression.md).
