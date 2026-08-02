# [[ ]]

## Use

```bash
[[ -e "$path" ]]
```

## What It Does

`[[ ]]` is Bash's conditional expression syntax. It tests strings, files, numbers, and patterns, then returns success or failure.

## File Tests

```bash
[[ -e "$path" ]]
[[ -f "$path" ]]
[[ -d "$path" ]]
[[ -x "$path" ]]
```

- `-e`: path exists.
- `-f`: regular file.
- `-d`: directory.
- `-x`: executable or searchable.

## String Tests

```bash
[[ -z "$name" ]]
[[ -n "$name" ]]
[[ "$name" == "Ada" ]]
[[ "$name" == A* ]]
```

- `-z`: empty string.
- `-n`: non-empty string.
- `==`: string match.
- Right side patterns such as `A*` are Bash patterns when unquoted.

## Numeric Tests

```bash
[[ "$count" -gt 0 ]]
[[ "$count" -eq 10 ]]
```

Use `-gt`, `-lt`, `-eq`, `-ne`, `-ge`, and `-le` for integer comparisons.

## Watch Out

- Keep spaces after `[[` and before `]]`.
- Quote variables unless you intentionally want pattern matching.
- `[[ ]]` is Bash syntax, not portable `/bin/sh` syntax.

## Docs Pointers

- Run `help [[`.
- Read [conditionals](../concepts/conditionals.md), [quoting](../concepts/quoting.md), and [if](if.md).
