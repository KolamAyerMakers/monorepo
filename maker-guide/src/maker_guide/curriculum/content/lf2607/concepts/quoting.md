# Quoting

## Core Idea

Quoting controls how Bash turns text into command arguments.

Most shell bugs are not command bugs. They are argument bugs caused by word splitting, glob expansion, or variables expanding at the wrong time.

## The Rule

Quote variables by default:

```bash
printf '%s\n' "$name"
```

Leave a variable unquoted only when you intentionally want Bash to split it or expand patterns.

## Single Quotes

Single quotes preserve text exactly. Bash does not expand variables inside them.

```bash
printf '%s\n' '$HOME'
```

Output:

```text
$HOME
```

Use single quotes for grep, sed, and awk programs unless you deliberately need shell expansion.

## Double Quotes

Double quotes preserve spaces but still allow variable and command substitution.

```bash
name='Ada Lovelace'
printf 'Hello %s\n' "$name"
```

Without quotes, Bash would split the name into two arguments.

## Backslash

Backslash protects one character or creates escapes interpreted by a command.

```bash
printf 'line one\nline two\n'
grep '\.org$' urls.txt
```

In the `grep` example, `\.` means a literal dot in the regular expression.

## Command Substitution

Quote command substitution too:

```bash
printf 'today=%s\n' "$(date +%F)"
```

## Globs

Shell globs expand before the command runs:

```bash
ls *.md
```

Quote a glob when you want the receiving command to see the pattern literally:

```bash
find ~/src -name '*.md'
```

## Proof Check

Set `name='Ada Lovelace'`, print it quoted and unquoted with `printf '[%s]\n'`, then explain the difference.

## Docs Pointers

- Run `man bash` and read `QUOTING`, `EXPANSION`, and `Word Splitting`.
- Read [variables](variables.md), [script arguments](script-arguments.md), [regular expressions](regular-expression.md), and [shell scripting](shell-scripting.md).
