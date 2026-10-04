# S02 topic coverage: legacy sources

Eight original A5 comic-reference pages for Linux beginners. S02 supplies the core
topics; SSH keys and the classroom website pipeline are deliberately excluded.
Plain explanations come before jokes and warnings. White backgrounds, black
linework and restrained pastel fills continue the approved visual direction.

[Current complete proof](../../local/at-the-prompt-original-knowledge-A5.pdf).
The table inventories sources, not reading order. Installation belongs to Package
Management; creation and editing to Files and Paths, redirection to Streams and
Pipes, and ownership to Ownership and Permissions. [The manifest](../contents.toml)
is authoritative.

| Page | Artwork | Purpose |
| :--- | :--- | :--- |
| 1 | `01-making.svg` | Create a directory with `mkdir`; explain missing parents and `-p`. |
| 1b | `01-touch.svg` | Create an empty file with `touch`; distinguish timestamps from contents. |
| 2 | `02-install.svg` | Install packages with apt or dnf; nano is the example package. |
| 3 | `03-editing.svg` | Open with nano; save with Ctrl-O and Enter; quit with Ctrl-X. |
| 4 | `04-redirection.svg` | Define echo and compare replacement with append using explicit input/output. |
| 5 | `05-copy-move.svg` | Explain copy versus rename/move, including destination overwrite risk. |
| 6 | `06-remove.svg` | Introduce `rm -i` before explaining the absence of a desktop recovery bin. |
| 7 | `07-owner.svg` | Define ownership and locate the owner's name in a concrete `ls -l` example. |

Grounding: S02 slides, recap and self-study under
`maker-guide/src/maker_guide/curriculum/content/lf2607/`. Nano is a deliberate
replacement for Micro, not a claim about the default editor on all distributions.
Installation is conditional, distro-labelled, and requires administrative
permission. The book shows installation commands but the assistant does not run
them. Nano's shortcut example uses its default bindings and default save prompt.

The ownership listing is an illustrative example, not output promised on every
computer. It highlights the owner without trying to teach all permission bits on
the same page. The explanation notes that ownership does not imply exclusive access.
Examples are independent references, not an exercise sequence.

See [editorial rules](../../AGENTS.md) and [fonts/palette](../../sample/README.md).
From `graduation/book`, export with installed Inkscape:

```bash
mkdir -p local/s02
for source in chapters/s02/*.svg; do
  name=$(basename "$source" .svg)
  inkscape "$source" --export-type=pdf --export-filename="local/s02/$name.pdf"
  inkscape "$source" --export-width=1260 --export-filename="local/s02/$name.png"
done
```

Merge in `../contents.toml` order. Old local key/website PDFs are superseded
and must not be picked up by a wildcard merge. Generated files stay ignored in
`local/`; no purchased material, new dependency or CI job is introduced.
