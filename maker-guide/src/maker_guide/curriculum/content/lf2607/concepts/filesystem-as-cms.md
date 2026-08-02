# Filesystem As CMS

## Core Idea

For this course, files under `~/src/pages/` are your content management system.

There is no hidden web dashboard. You publish by editing source files, running a build, and inspecting generated output.

## Source To Site

```text
~/src/pages/*.md -> build-website -> ~/public_html/*.html -> public HTTPS URL
```

This model is simple and honest: files are the source of truth, and generated HTML is output.

## Why It Matters

Command output can become durable documentation when you write it into Markdown. That turns shell work into a public page another person can read.

## Watch Out

Do not edit generated HTML as the permanent source. Rebuilds should be repeatable.

## Docs Pointers

- Read [Markdown basics](markdown-basics.md), [site source ownership](site-source-ownership.md), [build-website](../commands/build-website.md), and [HTML on the wire](html-on-the-wire.md).
