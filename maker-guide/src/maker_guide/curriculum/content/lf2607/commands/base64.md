# base64

## Use

```bash
printf 'hello\n' | base64
printf 'aGVsbG8K\n' | base64 -d
```

## What It Does

`base64` encodes or decodes base64 text.

Base64 turns arbitrary bytes into printable ASCII characters. It is useful for transport, not secrecy.

## Practice

The first command produces `aGVsbG8K`; the second decodes it to `hello` and a newline. `-d` means decode.

## Watch Out

Base64 is encoding, not encryption.

## Docs Pointers

- Run `man base64`.
- Read [file encoding](../concepts/file-encoding.md).
