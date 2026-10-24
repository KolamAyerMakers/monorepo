# S10 — Keep Learning After Class

Choose one environment, one small project, and one useful resource. This is not another assignment.

## Keep your work

The classroom server will close when cloud credits run out; no date is confirmed. After graduation, the planned follow-up email includes two archives:

- Your personal work tarball: the existing `~/scripts`, `~/src`, and `~/playground` folders, without `node_modules`. Reinstall project dependencies when needed.
- The course PDFs: session guides, reference cards, and the home setup guide.

Keep your own copies once received. You can continue without the classroom server.

The self-study pack contains the guides, home setup, worked answers, and a ZIP of practice files. It does not contain passwords, class tokens, or purchased Julia Evans PDFs. Your printed *At the Prompt* anthology remains your reading companion.

## Choose your Linux

Use **Ubuntu LTS** to repeat the course. One familiar environment is more useful than a week spent comparing distributions.

| Your computer | Recommended start |
|---|---|
| Windows | Ubuntu in WSL2 |
| Mac | Ubuntu in a VM, using UTM |
| Linux | Your Ubuntu LTS terminal |
| Spare PC | Ubuntu LTS, after backing up its files |

Follow [Continue at Home](../../guides/continue-at-home.md) for installation links, practice files, and a local site. It covers ARM64 for Apple Silicon and x86-64 for Intel machines.

A Mac terminal is already useful for files and pipes, but macOS is not Linux: options, shell defaults, and service management differ. Use Ubuntu for the Linux-specific exercises. No paid cloud account or domain is needed.

## Try a ten-minute experiment

In your Ubuntu terminal:

```bash
mkdir -p ~/playground/learning
cd ~/playground/learning
printf '%s\n' '$HOME'
printf '%s\n' "$HOME"
```

Predict before running the last two commands. Why are their results different? Change the example and predict again.

A question, prediction, experiment, and explanation make a complete practice session. [Compare the answer](../../guides/self-study-answers.md#s10-keep-learning).

## When something fails

1. Name the result you wanted and the result you got.
2. Read the exact error; look for a path, option, permission, or connection.
3. Form one hypothesis and choose one small test.
4. Inspect the result before changing anything else.
5. Leave a note of the next test if you stop.

Use `COMMAND --help` for an overview and `man COMMAND` for details. In the usual pager, `/word` searches, `n` finds the next match, and `q` quits. Start with your question, not every option.

### Ask for useful help

Share your goal, system/application version, command or configuration, exact error, and what you tested. Remove passwords, tokens, private keys, and personal data.

An AI tutor can explain a command or suggest a test. Ask **what the result would tell you** and verify claims against current official documentation. Understand a proposed change and how to undo it before approving it—especially deletion, disk operations, `sudo`, or security changes.

Sometimes investigate without AI first. Bring your actual observations when asking a person, forum, or project community. Explain the eventual solution so the next learner can use it too.

## Build something you want to use

Pick one first result—not the whole row of future possibilities:

| Interest | Small first result | Resource |
|---|---|---|
| Data | Save an API response and make a labelled report | Revisit S9; check units, limits, and terms |
| Media | Play one video you may legally use, then try another device on your home network | [Jellyfin docs](https://jellyfin.org/docs/) |
| Photos | Import a **copy** of a small sample; test export and restore | [Immich docs](https://immich.app/docs/) |
| Home automation | Read one sensor and make one useful automation | [Home Assistant](https://www.home-assistant.io/getting-started/) |
| Programming | Improve a course script or write a small Python quiz | [Python tutorial](https://docs.python.org/3/tutorial/) |
| Security puzzles | Investigate one authorized Linux challenge | [OverTheWire Bandit](https://overthewire.org/wargames/bandit/) |

A VM is enough to begin a homelab. Buy hardware only when you have a reason. Keep new services on your local machine or home network first; do not open router ports just to make a test work. Back up important files and test restoring them.

A project you can explain—its purpose, operation, one failure, and verified repair—is more useful than a copied setup you cannot maintain.

## Keep a small learning shelf

Use *At the Prompt* according to your current question:

| Zine | Reach for it when… |
|---|---|
| The Secret Rules of the Terminal | Terminal behaviour surprises you |
| Bite Size Command Line | You want to try or combine tools |
| Bite Size Linux | You want to understand the system |
| Bite Size Bash | You are writing or debugging a script |
| How Git Works | You want to understand changes and history |

For a structured path, [The Linux Command Line](https://linuxcommand.org/tlcl.php) has a free, legally downloadable PDF. Keep your course PDFs and your project's official docs nearby.

Read one page, try one example, and change something. If you return after a break, start with your next small test—not the beginning of every guide.
