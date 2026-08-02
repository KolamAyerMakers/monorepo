# awk

## Use

```bash
awk -F: '{print $1}' /etc/passwd
```

## What It Does

`awk` reads input as records, splits each record into fields, and runs a small program for each record.

By default, a record is one line and fields are separated by whitespace. `-F:` changes the field separator to colon.

## Mental Model

```bash
awk -F: '{print $1}' /etc/passwd
```

- `awk`: run awk.
- `-F:`: split each input line on `:`.
- `'{print $1}'`: awk program. Single quotes protect `$1` from Bash.
- `/etc/passwd`: input file.
- `$1`: first awk field, not the shell's first script argument.

## Examples

Print the first colon-separated field:

```bash
awk -F: '{print $1}' /etc/passwd
```

Print two fields with a label:

```bash
awk -F: '{print "user=" $1 " shell=" $7}' /etc/passwd
```

Print line numbers using awk's built-in `NR` variable:

```bash
awk '{print NR ": " $0}' ~/src/pages/index.md
```

Print only lines where the third field is at least `1000`:

```bash
awk -F: '$3 >= 1000 {print $1}' /etc/passwd
```

Count matching lines:

```bash
awk '/ssh/ {count += 1} END {print count}' ~/.bash_history
```

Sum numbers from the first field:

```bash
printf '1\n2\n3\n' | awk '{total += $1} END {print total}'
```

Change output separator with `OFS`:

```bash
awk 'BEGIN {OFS=","} {print $1, $2}' names.txt
```

Use awk in a pipeline:

```bash
ps aux | awk '$3 > 10 {print $1, $2, $3, $11}'
```

## Watch Out

- Use single quotes around awk programs so Bash does not expand `$1`, `$2`, or `$0`.
- `$0` means the whole input record in awk.
- Empty output usually means the pattern matched nothing or the field separator is wrong.
- Prefer awk for field-oriented text; prefer `sed` for simple substitutions.

## Docs Pointers

- Run `man awk`.
- Read [GNU awk manual](https://www.gnu.org/software/gawk/manual/gawk.html).
- Read [regular expressions](../concepts/regular-expression.md), [text transforms](../concepts/text-transforms.md), [one-liners](../concepts/oneliner.md), and [quoting](../concepts/quoting.md).
