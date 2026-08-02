# Shell Investigation

## Core Idea

Shell investigation means using small commands to turn an unknown system problem into evidence.

Bandit is not the concept. Bandit is practice. The transferable skill is evidence-driven investigation with files, permissions, encodings, search, and pipelines.

## Loop

1. Read the exact prompt or error.
2. Inspect the path with `ls -la`, `file`, or `stat`.
3. Read small text with `cat`, `less`, `head`, or `tail`.
4. Search with `grep` when output is large.
5. Use `strings`, `xxd`, or `base64` only when bytes stop being plain text.
6. Record the command that changed your understanding.

## Example Pattern

```bash
file suspicious
strings suspicious | less
strings suspicious | grep -i password
```

## Watch Out

Do not jump to random commands. Every command should answer one question.

## Docs Pointers

- Read [file](../commands/file.md), [strings](../commands/strings.md), [regular expressions](regular-expression.md), [file encoding](file-encoding.md), and [pipes](pipes.md).
