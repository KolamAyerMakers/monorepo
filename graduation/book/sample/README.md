# At the Prompt: original comic reference sample

Three A5 landscape comic pages, not a workbook. Each is a quick visual reminder:
one core idea, a small joke and a few reference labels. No exercises, assessment
questions, lesson sequence or command transcripts. Future pages can introduce
related ideas beyond the course, without becoming a comprehensive manual.

- [Revised three-page PDF](../local/sample/at-the-prompt-comic-sample-A5.pdf).
- [Paths preview](../local/sample/comic-01-paths.png).
- [Pipes preview](../local/sample/comic-02-pipes.png).
- [Git preview](../local/sample/comic-03-git.png).

The SVGs contain original words and illustrations. No purchased zine pages,
transcripts or xkcd artwork are reused. The visual direction is loose black
linework, uneven shapes, stick characters and handwritten lettering. Characters,
dialogue and compositions are newly drawn for this sample. Rounded hair, curls,
glasses, tied-back hair and a seated broader clerk replace the paired pointed
tufts and repeated default silhouette. No horn-like hair or single protagonist.

Colour stays light: white paper, black lettering and linework, with small mint
`#def1e8`, butter-yellow `#fff0c9`, lavender `#ece5f5` and blush `#f8e0dc` accents.
Highlights sit behind useful objects or labels, never behind an entire page.
Colour is supplementary: labels, arrowheads and structure still work in grayscale.

## Curriculum grounding

Sources are relative to
`maker-guide/src/maker_guide/curriculum/content/lf2607/`:

| Page | Sources | Reminder and extra connection |
| :--- | :--- | :--- |
| cd: change directory. | `concepts/filesystem.md`, `concepts/filesystem-navigation.md` | Prominent `cd ../notes` moves between sibling directories; `..` names their parent. |
| Pipes: connect commands. | `sessions/S03/recap.md`, `quests/count-stream.md` | Small programs cooperate; stderr has its own route. |
| Git's staging area. | `commands/git-add.md`, `commands/git-commit.md` | Staging captures a version; later edits need another `git add`. |

The comic is a mnemonic, not the entire technical model. In particular, Git's
staging area is not a person or a second ordinary file, and a pipe carries bytes,
not sheets of paper. The labels retain the real concepts alongside the metaphor.

## Edit and export

Each SVG is 210 × 148 mm. Artwork remains vector and text remains editable.
Lettering uses the installed Chilanka handwriting font, with Liberation Mono for
command labels. Install Chilanka and Liberation fonts
to reproduce the appearance; Inkscape embeds the used fonts in exported PDFs.
No new Python code, dependency or CI job is needed for these static SVG pages.

From `graduation/book`:

```bash
mkdir -p local/sample
for source in sample/0*.svg; do
  name=$(basename "$source" .svg)
  inkscape "$source" --export-type=pdf --export-filename="local/sample/comic-$name.pdf"
  inkscape "$source" --export-width=1260 --export-filename="local/sample/comic-$name.png"
done
```

Generated PDFs and previews remain ignored under `local/`. Earlier workbook
proofs are superseded; the approved purchased anthology is unchanged. This is
an editorial sample, not a printer-ready export with bleed or punching allowance.

The complete book reuses these sources in the explicit knowledge-based order in
[`../chapters/contents.toml`](../chapters/contents.toml). Review jokes, labels and
character variety in the [current proof](../local/at-the-prompt-original-knowledge-A5.pdf).

Illustration review: every label must belong clearly to an object or action;
command syntax must match the pictured flow, including visible pipe symbols;
inputs and outputs must agree; recurring characters must retain their identifying
features. Remove stray labels rather than explaining them in extra prose.
Use unmistakable arrowheads for movement; keep arrow routes clear of text,
characters and other connectors. Do not mix tree branches with navigation arrows
when the extra lines make the intended path ambiguous.
