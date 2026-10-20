# Concept: Manual Pages

Manual pages are built-in documentation.

```bash
man ls
```

In the usual `less` pager, `/pattern` searches, `n` finds the next match, Space advances, and `q` quits. Try searching for `--all` in `man ls`.

The number in a page name identifies its section: `man 1 passwd` describes the command, while `man 5 passwd` describes the file format. Bash builtins such as `cd` have help inside Bash: use `help cd`.
