# README Writing

## Core Idea

A README tells future readers what the project is, how it works, and how to run it.

## Practice Alone

Start with a fresh temporary file:

```bash
work=$(mktemp -d)
micro "$work/README.md"
```

Describe one script or project you actually have. Include:

- What it does and what its output means.
- Required tools and input files.
- A command to run it, including the directory to run from.
- How to check success and stop/undo temporary work.
- One common failure and the next diagnostic step.

Include a build command or URL only if the project has one. Do not put credentials or private recovery links in a README.

## Done When

Follow your own instructions from a new terminal. They should identify any setup needed without relying on your current directory or shell variables.
