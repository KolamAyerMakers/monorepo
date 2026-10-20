# Site Source Ownership

## Core Idea

Your site has source and output.

- Source: content, layouts, configuration, and build scripts.
- Output: HTML and other files generated from that source.

Edit source. Rebuild output. If output breaks, rebuild it. If source breaks, fix the source carefully.

## Trace one change

Use the complete setup from [First Site Build](first-site-build.md), which introduces source files and their builder. Change one heading in its Markdown source, rebuild successfully, then locate the heading in generated HTML and in an actual GET response.

Markdown source is meant for editing; HTML output is meant for the browser. A filesystem name, generated filename, and URL path need not be identical.

## Common Failure

- An edit made only to generated HTML disappears at the next build.
- Committing output alone leaves out the content and instructions needed to rebuild it.
- Forgetting to build leaves the served page behind your source edits.

## Done When

You can explain which file you edit, which command rebuilds output, and which generated file the public URL serves.

## Docs Pointers

- Read [build-website](../commands/build-website.md), [first site build](first-site-build.md), and [filesystem as CMS](filesystem-as-cms.md).
