# Markdown Basics

## Core Idea

Markdown is plain text with lightweight structure. It is readable in the terminal and easy to convert into HTML.

## Common Syntax

Heading:

```markdown
# My Page
```

Paragraph:

```markdown
This is normal text.
```

List:

```markdown
- First point
- Second point
```

Link:

```markdown
[Kolam Ayer Makers](https://kolamayermakers.org/)
```

Inline code:

```markdown
Run `build-website` after editing.
```

Fenced code block:

````markdown
```bash
pwd
ls
```
````

## Source Versus Output

Your source Markdown lives under `~/src/pages`. `build-website` turns it into generated HTML under `~/public_html`.

Edit Markdown source. Treat generated HTML as output.

## Practice Alone

Create a page with a heading, one paragraph, one link, one list, and one fenced code block. Build it and inspect the public page.

## Done When

You can explain which file is source Markdown and which file is generated HTML.

## Docs Pointers

- Read [CommonMark help](https://commonmark.org/help/).
- Read [build website](../commands/build-website.md), [site source ownership](site-source-ownership.md), and [HTML on the wire](html-on-the-wire.md).
