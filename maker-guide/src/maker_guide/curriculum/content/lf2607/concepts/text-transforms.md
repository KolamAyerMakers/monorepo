# Text Transforms

## Core Idea

Linux tools can reshape text without opening an editor.

## Practice Alone

Use `sed` for substitutions and `awk` for fields.

```bash
printf 'hello makers\n' | sed 's/makers/world/'
printf 'Ada:42\nGrace:31\n' | awk -F: '{print $1}'
```

Expect `hello world`, then `Ada` and `Grace` on separate lines. Single quotes keep Bash from expanding awk's `$1`; here it means the first colon-separated input field, not a script argument.

## Done When

You can transform a line and extract a field from a structured file.

## Go Deeper

- [One-liners](oneliner.md) explains why `sed` and `awk` often appear inside one-line shell programs.
- [Regular expressions](regular-expression.md) explains the matching side of `sed` substitutions.
- Quoting decides whether Bash or the text tool sees `$1`.
