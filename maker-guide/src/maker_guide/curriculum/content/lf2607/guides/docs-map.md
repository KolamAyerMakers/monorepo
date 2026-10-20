# Find the Guide You Need

Start with your question, not a reading list.

| You want to… | Open |
|---|---|
| Repeat an exercise | That session's self-study guide |
| Check syntax or an option | [Command cards](../commands/README.md) |
| Understand why something works | [Concept cards](../concepts/README.md) |
| Compare your reasoning | [Worked Answers](self-study-answers.md), after trying |
| Practise after the server closes | [Continue at Home](continue-at-home.md) |
| Find a classroom address or path | [Platform Reference](platform-reference.md) |

## Reading PDFs

Keep the bundle's folders together so links between PDFs can work. Start with `guides/continue-at-home.pdf`; session guides are under `sessions/S01` through `sessions/S10`. Use your reader's search function for a command or exact error.

The practice ZIP also contains searchable Markdown in `reading/`. Copy long commands from those files rather than retyping wrapped PDF lines.

## Reading in a terminal

**In class**, the course map shows released material:

```bash
less /docs/README.md
```

Choose your document root before using the relative paths below:

- Classroom: `cd /docs`
- Home kit: `cd ~/linux-foundations-practice/reading`

```bash
ls
less commands/README.md
less concepts/README.md
```

In `less`, Space advances, `b` goes back, `/word` searches, `n` finds the next match, and `q` quits. Classroom `glow -p PATH` is an optional Markdown viewer; `less` needs no extra setup.

## Follow a Markdown link

```markdown
[SSH](../commands/ssh.md)
```

The text in parentheses is the target. A relative link starts from **the document's directory**, not your shell's current directory. From the document root chosen above, open this example with `less commands/ssh.md`.

An absolute path such as `/docs/commands/ssh.md` works from any classroom directory, but `/docs` does not exist automatically at home.

## Find a topic

From your document root:

```bash
find . -iname '*ssh*'
grep -Rni 'ssh key' .
```

`find` searches filenames. `grep` searches file contents and reports matching paths and line numbers. Open a match with `less PATH`; replace `PATH` with the result you want.

If the material does not answer your question, ask with your goal, command, exact error, and what you already checked. Remove passwords, tokens, private keys, and personal data.
