# Shell Investigation

## Core Idea

Shell investigation means using small commands to turn an unknown system problem into evidence.

Choose a command that answers one question, then use its result to choose the next.

## Loop

1. Read the exact prompt or error.
2. Inspect the path with `ls -la`, `file`, or `stat`.
3. Read small text with `cat`, `less`, `head`, or `tail`.
4. Search with `grep` when output is large.
5. Use `strings`, `xxd`, or `base64` only when bytes stop being plain text.
6. Record the command that changed your understanding.

## Example Pattern

```bash
work=$(mktemp -d)
printf 'header\0maker-note\0' > "$work/sample.bin"
file "$work/sample.bin"
xxd "$work/sample.bin"
strings "$work/sample.bin"
```

## Watch Out

`xxd` exposes the `00` separator bytes; `strings` extracts readable runs but omits those separators. Neither command executes the file. Do not infer that a file is safe to run merely because it contains readable text.

## Docs Pointers

- Read [file](../commands/file.md), [strings](../commands/strings.md), [regular expressions](regular-expression.md), [file encoding](file-encoding.md), and [pipes](pipes.md).
