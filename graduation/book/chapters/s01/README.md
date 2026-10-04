# S01 topic coverage: legacy sources

Nine original A5 comic-reference pages, using S01 as a topic map but written for
beginners on their own Linux computer. No classroom commands, website build,
custom paths or chat channels. The purchased anthology is unchanged.

[Current complete proof](../../local/at-the-prompt-original-knowledge-A5.pdf).
These sources now belong to Terminal and Commands, Files and Paths, and Remote
Terminals with SSH. [The manifest](../contents.toml) determines reading order;
the table below inventories original source positions, not a chapter sequence.

## Source inventory

| Page | Artwork | Beginner-facing purpose |
| :--- | :--- | :--- |
| 1 | `01-connection.svg` | Explain terminal, shell and an optional SSH connection to another computer. |
| 2 | `02-command.svg` | Decode `ls -la /etc`, including options and the displayed prompt. |
| 3 | `03-bearings.svg` | Find the account, computer name, time and time since startup. |
| 4 | `../../sample/01-paths.svg` | Follow a relative path through its parent directory. |
| 5 | `05-map.svg` | Define `/` as filesystem root and `~` as the user's home. |
| 6 | `06-dotfiles.svg` | Explain leading-dot names and how `ls -a` includes them. |
| 7 | `07-reading.svg` | Choose whole-file, first-lines, last-lines or scrolling views of text. |
| 8 | `08-recovery.svg` | Recall Bash keys and look up a command with `man`. |
| 9 | `09-help.svg` | Give the exact command and error when asking for help. |

Grounding: `sessions/S01/slides.md`, `recap.md`, `self-study.md` and the terminal
and filesystem concept cards in
`maker-guide/src/maker_guide/curriculum/content/lf2607/`. Classroom-specific
material and optional conveniences such as tldr and tree are deliberately omitted.
Common Linux tools are not guaranteed on every minimal installation. Nano and
distribution-specific installation are introduced in Package Management, which
follows Terminal and Commands and precedes Files and Paths.

Editorial and illustration rules are in [AGENTS.md](../../AGENTS.md). Fonts and
pastel palette follow the [sample](../../sample/README.md). Text is black on white;
small fills highlight objects, not whole pages. The navigation source is reused,
not duplicated.

## Export locally

From `graduation/book`, with Inkscape, Chilanka and Liberation fonts installed:

```bash
mkdir -p local/s01
for source in chapters/s01/*.svg; do
  name=$(basename "$source" .svg)
  inkscape "$source" --export-type=pdf --export-filename="local/s01/$name.pdf"
  inkscape "$source" --export-width=1260 --export-filename="local/s01/$name.png"
done
inkscape sample/01-paths.svg --export-type=pdf --export-filename="local/s01/04-paths.pdf"
```

Use `../contents.toml` when merging; do not glob old PDFs from `local/`.
Earlier classroom-oriented proofs are superseded. Generated files remain ignored;
this is an editorial review proof, not a printer-approved export.
