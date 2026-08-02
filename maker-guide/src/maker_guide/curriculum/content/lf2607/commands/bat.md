# Command: `bat`

`bat` prints files with syntax highlighting, line numbers, and paging.

```bash
bat ~/src/pages/index.md
bat --plain /etc/os-release
```

`bat` is a good everyday replacement for both `cat` and `less` when you are reading code, Markdown, or configuration files interactively. It is not the true standard: `cat` and `less` are available on almost every Unix-like system, while `bat` may be missing on minimal servers.

Use `cat` for tiny files, exact proof output, and pipelines where extra formatting would get in the way. Use `less` when `bat` is unavailable and you need paging.

## Watch Out

`bat` is a reader, not an editor. If output looks decorated, rerun with `--plain` before copying proof into chat. If a command or script must work on any normal server, write it with `cat` or `less`, not `bat`.

## Docs Pointers

- Run `bat --help`.
- Read [Command: `cat`](cat.md), [Command: `less`](less.md), and [Concept: Reading Files](../concepts/reading-files.md).
