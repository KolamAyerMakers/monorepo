# First Site Build

## Core Idea

A build converts source files into deliverable output. Serving and inspecting that output is a separate step.

```text
Markdown source -> build -> generated HTML -> HTTP server -> browser
```

## Choose the setup

- **At home:** [Continue at Home](../guides/continue-at-home.md) supplies the Astro starter, Node installation, build command, and loopback preview.
- **In class:** [build-website](../commands/build-website.md) initializes the platform project; [Platform Reference](../guides/platform-reference.md) gives its addresses.

Complete one setup before trying to inspect its output. The classroom helper is not a Linux command available everywhere.

## What To Verify

- You know which source file you edited.
- The setup's build command finishes successfully.
- The generated HTML contains the change.
- An actual GET response and the browser show that same change.

## Diagnose the missing stage

A build error is not a network error. A generated file does not prove the server can reach it. HTTP `200` does not prove the body is the page you intended. Compare the source, output, response body, and browser instead of repeating the build blindly.

## Docs Pointers

- Read [build-website](../commands/build-website.md), [Markdown basics](markdown-basics.md), [filesystem as CMS](filesystem-as-cms.md), and [platform reference](../guides/platform-reference.md).
