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
Run `pwd` to print the current directory.
```

Fenced code block:

````markdown
```bash
pwd
ls
```
````

The optional word after the opening triple backticks describes the content. Use `bash` for Bash source and `text` for plain command output:

````markdown
```text
/bin/bash
/usr/sbin/nologin
```
````

## Source Versus Output

Markdown source is text you edit; a renderer converts it into HTML or another format. The original `.md` file and generated `.html` file are different documents.

Edit Markdown source. Treat generated HTML as output.

## Practice Alone

Use a new file in a fresh temporary directory:

```bash
work=$(mktemp -d)
micro "$work/page.md"
cat "$work/page.md"
```

Add a heading, paragraph, link, list, and fenced code block using the examples above. Save with `Ctrl-S` and quit with `Ctrl-Q`. For a complete rendered site example, follow [First Site Build](first-site-build.md); reading Markdown alone does not require a build.

## Done When

You can explain which file is source Markdown and which file is generated HTML.

## Docs Pointers

- Read [CommonMark help](https://commonmark.org/help/).
- Read [build website](../commands/build-website.md), [site source ownership](site-source-ownership.md), and [HTML on the wire](html-on-the-wire.md).
