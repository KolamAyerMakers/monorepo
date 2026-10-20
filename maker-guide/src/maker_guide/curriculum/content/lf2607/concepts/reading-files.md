# Concept: Reading Files

Choose a reader according to the file and the question:

Use `cat` for short plain output, `bat` for highlighted interactive reading, `less` for longer files, `head` for the beginning, and `tail` for the end.

```bash
cat /etc/os-release
head -n 5 /etc/services
tail -n 5 /etc/services
less /etc/services
```

In `less`, `/ssh` searches for `ssh`, `n` finds the next match, and `q` quits. For an unknown file, run `file PATH` first instead of sending arbitrary binary bytes to the terminal.

## Go Deeper

- [File](file.md) explains file content and metadata.
- [File Encoding](file-encoding.md) explains why bytes need an encoding before they become text.
- [I/O](io.md) explains input and output streams.
