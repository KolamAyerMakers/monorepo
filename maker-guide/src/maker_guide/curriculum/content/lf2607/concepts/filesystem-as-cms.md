# Filesystem As CMS

## Core Idea

CMS means content management system. For a file-based site, text files hold the content rather than a web dashboard or database.

There is no hidden web dashboard. You publish by editing source files, running a build, and inspecting generated output.

## Source To Site

```text
Markdown files -> site build -> generated HTML -> HTTP server -> browser
```

The files are the source of truth; HTML is rebuildable output. Git can record the source's history, and scripts can generate new pages.

## Why It Matters

Command output can become durable documentation when you write it into Markdown. That turns shell work into a public page another person can read.

For a complete local example with its own starter files, follow [Continue at Home](../guides/continue-at-home.md). No hosted account or public domain is needed.

## Watch Out

Do not edit generated HTML as the permanent source. Rebuilds should be repeatable.

## Docs Pointers

- Read [Markdown basics](markdown-basics.md), [site source ownership](site-source-ownership.md), [build-website](../commands/build-website.md), and [HTML on the wire](html-on-the-wire.md).
