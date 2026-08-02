# Command: `find`

## Use

```bash
find ~ -maxdepth 2 -type f
```

## What It Does

`find` walks directory trees and prints paths that match rules.

## Examples

Find files under your source tree:

```bash
find ~/src -type f
```

Limit depth while learning:

```bash
find ~ -maxdepth 2 -type d
```

Find Markdown files:

```bash
find ~/src/pages -name '*.md'
```

Find recently changed files:

```bash
find ~/src -type f -mtime -1
```

Find empty directories:

```bash
find ~/playground -type d -empty
```

Ignore permission noise when deliberately searching system paths:

```bash
find /etc -name '*.conf' 2>/dev/null
```

## Watch Out

Quote glob patterns such as `'*.md'` so the shell does not expand them before `find` receives them.

Start shallow. Searching `/` can be slow and noisy.

## Docs Pointers

- Run `man find`.
- Read [path](../concepts/path.md), [filesystem](../concepts/filesystem.md), [regular expressions](../concepts/regular-expression.md), and [stream redirection](../concepts/stream-redirection.md).
