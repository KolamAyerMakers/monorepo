# Command: `bat`

`bat` prints files with syntax highlighting, line numbers, and paging.

```bash
bat /etc/services
bat --plain /etc/os-release
```

Use `bat` for highlighted reading when installed; Ubuntu's package may name it `batcat`. Use `cat` for plain output or `less` for paging without highlighting.

Press `q` to leave its pager. Do not install an extra reader just to complete an exercise.

## Watch Out

`bat` is a reader, not an editor. If output looks decorated, rerun with `--plain` before copying proof into chat. If a command or script must work on any normal server, write it with `cat` or `less`, not `bat`.

## Docs Pointers

- Run `bat --help`.
- Read [Command: `cat`](cat.md), [Command: `less`](less.md), and [Concept: Reading Files](../concepts/reading-files.md).
