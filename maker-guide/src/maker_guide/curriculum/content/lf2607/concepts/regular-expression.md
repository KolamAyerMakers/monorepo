# Regular Expression

## Core Idea

A regular expression is a pattern for matching text.

`grep`, `sed`, and many other Unix tools use regular expressions to find the lines or parts of lines that matter. A regular expression is not the same thing as a shell glob.

## First Patterns

Literal text:

```bash
grep 'makers' ~/src/pages/index.md
```

Line starts with `#`:

```bash
grep '^#' ~/src/pages/index.md
```

Line ends with `.org`:

```bash
grep '\.org$' ~/src/pages/index.md
```

Any character:

```bash
grep 'h.t' words.txt
```

Zero or more of the previous thing:

```bash
grep 'lo*l' words.txt
```

## Small Vocabulary

| Pattern | Meaning |
|---|---|
| `abc` | Literal text `abc`. |
| `.` | Any one character. |
| `*` | Zero or more of the previous atom. |
| `^` | Start of line. |
| `$` | End of line. |
| `[abc]` | One character: `a`, `b`, or `c`. |
| `[^abc]` | One character that is not `a`, `b`, or `c`. |
| `\.` | Literal dot. |

## Regex Is Not Shell Glob

Shell glob:

```bash
ls *.md
```

The shell expands `*.md` into matching filenames before `ls` runs.

Regular expression:

```bash
grep '\.md$' file-list.txt
```

`grep` receives the pattern and matches it against text lines.

## Basic Versus Extended

Different tools use slightly different regex dialects.

In this course:

- `grep 'pattern' file` uses basic regular expressions by default.
- `grep -E 'pattern' file` uses extended regular expressions.
- `sed 's/pattern/replacement/'` uses basic regular expressions by default.
- Basic `sed` capture groups are written as `\( ... \)` and reused as `\1`.

This is why the course sed example looks like this:

```bash
sed 's/^# \(.*\)$/<h1>\1<\/h1>/'
```

## Common Failures

- Pattern matches too much: add anchors such as `^` or `$`.
- Dot matches any character: escape it as `\.` when you mean a literal dot.
- Shell changes the pattern: put regex patterns inside single quotes.
- `*` surprises you: it repeats the previous atom; it does not mean the same thing as shell `*`.
- Sed capture fails: use `\(...\)` in basic sed, not plain `(...)`.

## Proof Check

Create a scratch file with headings, ordinary lines, and a URL. Use `grep '^#'`, `grep '\.org$'`, and one `sed` substitution. Explain which characters were literal and which were regex syntax.

## Docs Pointers

- Run `man grep` and search for `REGULAR EXPRESSIONS`.
- Run `man 7 regex`.
- Run `man sed` and search for `REGULAR EXPRESSIONS`.
- Read [text search](text-search.md), [pipes](pipes.md), and [text transforms](text-transforms.md).
