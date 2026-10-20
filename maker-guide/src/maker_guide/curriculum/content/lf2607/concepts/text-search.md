# Text Search

## Core Idea

Most Linux troubleshooting starts by finding the line that matters.

## Practice Alone

Search a known file with `grep`, then use `grep` output as input to another command.

```bash
grep -n 'ssh' /etc/services
grep 'ssh' /etc/services | wc -l
```

The first command reports matching lines with their line numbers. The second counts matching lines, not occurrences of the word. `grep -F` treats a pattern as literal text; plain grep uses a regular expression.

## Done When

You can search a file or stream and understand every printed match. Recursive directory search comes later.

## Go Deeper

- [Regular expressions](regular-expression.md) explains pattern syntax for `grep`.
- [Pipes](pipes.md) explains how to search command output.
