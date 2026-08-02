# vim

## Use

```bash
vim ~/playground/vim-note.txt
```

## What It Does

`vim` is a modal text editor. Keys mean different things in normal mode, insert mode, command-line mode, and visual mode.

Use `nvim` when it is available. Neovim keeps the same core editing model and is often the better default on modern systems.

## Survival Path

Open a scratch file:

```bash
vim ~/playground/vim-note.txt
```

Then:

1. Press `i` to enter insert mode.
2. Type text.
3. Press Esc to return to normal mode.
4. Type `:wq` and press Enter to save and quit.

## Panic Table

| Situation | Keys |
|---|---|
| Start typing text | `i` |
| Leave insert mode | Esc |
| Save | Esc, `:w`, Enter |
| Save and quit | Esc, `:wq`, Enter |
| Quit without saving | Esc, `:q!`, Enter |
| Search | Esc, `/text`, Enter |
| Next search result | `n` |
| Undo | Esc, `u` |

## Core Movements

Learn these after survival works:

- `h`, `j`, `k`, `l`: left, down, up, right.
- `w`: next word.
- `b`: previous word.
- `0`: start of line.
- `$`: end of line.
- `gg`: top of file.
- `G`: bottom of file.

## Practice Game

Use [Vim Adventures](https://vim-adventures.com/) to build the movement model without damaging files.

## Watch Out

If vim shows a swap warning, read it. It may mean the file is already open in another terminal. For a scratch file, recover or quit after confirming no other edit is active.

## Docs Pointers

- Run `man vim` or `man nvim`.
- Inside nvim, type `:Tutor`.
- Read [Vim help online](https://vimhelp.org/) and [vim survival](../concepts/vim-survival.md).
