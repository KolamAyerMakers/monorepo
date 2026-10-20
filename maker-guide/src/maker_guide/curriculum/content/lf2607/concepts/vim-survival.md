# Vim Survival

## Core Idea

You do not need to love vim, but you must be able to save and escape it.

The most important fact: vim has modes. In normal mode, keys are commands. In insert mode, keys become text.

## Practice Alone

Open a scratch file, press `i`, type text, press Esc, type `:wq`, and verify with `cat`.

```bash
work=$(mktemp -d)
vim "$work/vim-note.txt"
cat "$work/vim-note.txt"
```

Minimum survival keys:

- `i`: enter insert mode.
- Esc: return to normal mode.
- `:wq`: write and quit.
- `:q!`: quit without saving.

## Watch Out

- If typing letters does not insert text, press `i`.
- If commands appear in the file, press Esc, then undo with `u` or quit with `:q!`.
- Use `micro` if you prefer a modeless editor; these shortcuts also help when another program opens Vim unexpectedly.

## Done When

Vim is no longer a trap.

## Docs Pointers

- Read [vim](../commands/vim.md) and [file editing](file-editing.md).
