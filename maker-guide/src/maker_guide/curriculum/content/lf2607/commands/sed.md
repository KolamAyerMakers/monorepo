# sed

## Use

```bash
printf 'hello makers\n' | sed 's/makers/world/'
```

## What It Does

`sed` transforms text as it streams through editing rules. Most beginner use is substitution.

## Simple Substitutions

Replace the first match on each line:

```bash
printf 'hello makers\n' | sed 's/makers/world/'
```

Replace every match on each line:

```bash
printf 'ha ha ha\n' | sed 's/ha/HA/g'
```

Use a different delimiter when the pattern contains `/`:

```bash
printf 'https://example.org\n' | sed 's#https://#http://#'
```

Delete blank lines:

```bash
sed '/^$/d' notes.txt
```

Print only lines 1 through 5:

```bash
sed -n '1,5p' notes.txt
```

## Capture Example

```bash
printf '# heading\n' | sed 's/^# \(.*\)$/<h1>\1<\/h1>/'
```

- `s/old/new/` means substitute.
- `^` anchors the start of the line.
- `$` anchors the end.
- `\(.*\)` captures text in basic sed regex.
- `\1` reuses the captured text.
- `<\/h1>` escapes `/` because `/` is the delimiter.

## In-Place Editing

Use in-place editing only after testing without it:

```bash
cp page.html page.html.backup
sed 's/old/new/' page.html
sed -i 's/old/new/' page.html
```

`sed -i` changes the file. Test on stdout first.

## Watch Out

- Keep sed scripts in single quotes so Bash does not alter them.
- If output is unchanged, the pattern did not match.
- If `\1` fails, you did not create a capture group in sed's regex dialect.

## Docs Pointers

- Run `man sed`.
- Read [GNU sed manual](https://www.gnu.org/software/sed/manual/sed.html).
- Read [regular expressions](../concepts/regular-expression.md), [text transforms](../concepts/text-transforms.md), [quoting](../concepts/quoting.md), and [awk](awk.md).
