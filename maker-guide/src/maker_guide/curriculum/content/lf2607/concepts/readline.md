# Readline

Readline is the line-editing library that gives Bash prompts many of their movement, editing, search, and history keystrokes.

## Movement

| Keys | Action |
|---|---|
| `Ctrl-A` | Move to start of line. |
| `Ctrl-E` | Move to end of line. |
| `Alt-B` | Move back one word. |
| `Alt-F` | Move forward one word. |
| `Ctrl-XX` | Toggle between current cursor position and start of line. |

## Editing

| Keys | Action |
|---|---|
| `Ctrl-U` | Cut from cursor to start of line. |
| `Ctrl-K` | Cut from cursor to end of line. |
| `Ctrl-W` | Cut the word before the cursor. |
| `Alt-D` | Cut the word after the cursor. |
| `Ctrl-Y` | Paste the last cut text. |
| `Ctrl-T` | Swap the two characters before the cursor. |
| `Alt-T` | Swap the two words around the cursor. |
| `Alt-U` | Uppercase from cursor to end of word. |
| `Alt-L` | Lowercase from cursor to end of word. |
| `Alt-C` | Capitalize from cursor to end of word. |

## History

| Keys | Action |
|---|---|
| Up | Previous command. |
| Down | Next command. |
| `Ctrl-R` | Reverse-search command history. |
| `Ctrl-G` | Cancel history search. |
| `Ctrl-P` | Previous history entry. |
| `Ctrl-N` | Next history entry. |

## Completion And Control

| Keys | Action |
|---|---|
| Tab | Complete command, path, variable, or option when possible. |
| Tab Tab | Show possible completions. |
| `Ctrl-C` | Interrupt the foreground command. |
| `Ctrl-D` | Send end-of-file; at an empty prompt, usually log out. |
| `Ctrl-L` | Clear the screen like `clear`. |

## Muscle Memory Drills

Type this line, but do not press Enter:

```bash
grep -n ssh /etc/services > ~/playground/matches.txt
```

Drill it:

1. Press `Ctrl-A`, add `time `, then press `Ctrl-E`.
2. Press `Alt-B` until the cursor reaches `ssh`, then change it to another word.
3. Press `Ctrl-K`, then `Ctrl-Y` to cut and restore the redirect.
4. Press `Ctrl-U`, then `Ctrl-Y` to cut and restore the whole command prefix.
5. Press `Ctrl-C` to cancel instead of running the practice line.

## Shell Ninja Habits

- Use Tab before typing the rest of a long path.
- Use `Ctrl-A` and `Ctrl-E` instead of holding arrow keys.
- Use `Ctrl-R` to search history instead of retyping old commands.
- Use `Ctrl-U` to clear a bad line instead of backspacing for ten seconds.
- Use `Ctrl-C` to cancel a half-written command safely.

## Docs Pointers

- Run `man bash`, then search for `READLINE`.
- Run `bind -P | less` to inspect active Readline bindings.
- Read the [GNU Readline manual](https://tiswww.case.edu/php/chet/readline/readline.html).
