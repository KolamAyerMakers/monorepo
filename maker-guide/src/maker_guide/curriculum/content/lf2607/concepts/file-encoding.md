# File Encoding

## Core Idea

Files contain bytes. Text files are bytes interpreted through an encoding. UTF-8 is the modern default for most Linux text because it can represent plain ASCII and many world writing systems without switching encodings.

## Commands To Try

```bash
printf 'makers\n' > ~/playground/encoding.txt
file ~/playground/encoding.txt
xxd ~/playground/encoding.txt
```

`file` guesses the file type. `xxd` shows the bytes. The ASCII letters in `makers` appear as hexadecimal bytes `6d 61 6b 65 72 73`.

## Newlines Matter

Unix text files usually end lines with one byte: line feed, shown as `0a` in hex. Windows text files often use carriage return plus line feed, shown as `0d 0a`. Scripts copied from Windows can fail if the shebang line ends with `0d 0a`.

## Common Confusions

- ASCII is a small 7-bit character set. UTF-8 is a Unicode encoding that preserves ASCII byte values.
- File extensions do not prove encoding.
- `cat` is useful for normal text, but `xxd` is safer when bytes matter.
- A file can be valid bytes but still not valid text in the encoding you expected.
- Binary does not mean dangerous. It means the file is not plain text.
- Base64 is reversible encoding for transport, not encryption.

## Binary Inspection

Use this first pass when a file is not obviously text:

```bash
file unknown
strings unknown | less
xxd unknown | head
```

`strings` extracts readable runs. `xxd` shows exact bytes. Neither replaces understanding the file format.

## Proof Check

Run `printf 'A\n' | xxd`. Explain why `41` is `A` and `0a` is the newline.

## Docs Pointers

- Run `man file`, `man xxd`, and `man locale`.
- Run `man strings` and `man base64` for binary inspection and transport encodings.
- Read [The Absolute Minimum Every Software Developer Absolutely, Positively Must Know About Unicode and Character Sets](https://www.joelonsoftware.com/2003/10/08/the-absolute-minimum-every-software-developer-absolutely-positively-must-know-about-unicode-and-character-sets-no-excuses/).
- Read [UTF-8 on Wikipedia](https://en.wikipedia.org/wiki/UTF-8) after you have looked at bytes with `xxd`.
