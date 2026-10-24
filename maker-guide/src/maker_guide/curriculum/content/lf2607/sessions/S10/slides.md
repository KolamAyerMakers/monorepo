# This Is Just The Beginning

Session: S10

2026-10-24

The course ends. Your learning does not.

**Today:** ideas for what comes next, then an open Q&A—ask anything.

**3pm:** graduation ceremony. Your families are welcome.

<!-- end_slide -->

# You Have A Foundation

- Find files, processes, and services.
- Write scripts and use data from an API.
- Read errors and logs. Investigate. Repair.

**You know enough to start something of your own.**

<!-- end_slide -->

# Linux Is Your Workshop

Programming. Data. Networks. Electronics. Robotics. Home automation. AI.

You do not need to become a Linux specialist.

Linux gives you tools to explore all of these.

<!-- end_slide -->

# Start A Homelab

One option: your own small collection of services, built to use and understand.

| Idea | First useful result |
|---|---|
| Media server | Watch your own videos with Jellyfin |
| Retro gaming | Play a homebrew game on an old PC or Pi |
| Video surveillance | View your own camera on your local network |
| Game server | Play with a friend on your own server |
| Home automation | Read a sensor or control a lamp |
| Photo library | Browse a small collection of your own photos |

**Pick one. Run it locally. Use it.**

<!-- end_slide -->

# Let It Grow One Step At A Time

For example, a Jellyfin media server:

1. Jellyfin plays one video.
2. Another device can watch it.
3. You understand its files, permissions, service, and logs.
4. You back it up—and test a restore.
5. You add something else you want.

Keep it local at first. Learn secure access before exposing services online.

<!-- end_slide -->

# Build Beyond The Terminal

A homelab is just one option. Your next project could look very different:

- **A robot** that maps a room and finds its way around furniture.
- **A plant monitor** that records soil moisture and alerts you when it's dry.
- **A camera** that recognises birds visiting your balcony.
- **A local AI assistant** that searches your own notes and manuals.
- **A time-lapse camera** that captures a plant growing over several weeks.
- **A neighbourhood sensor station** that maps temperature, noise, or air quality.
- **An interactive artwork** that changes its lights or sound when someone approaches.

<!-- end_slide -->

# Start With What You Already Have

| What you have | What to do |
|---|---|
| Your main computer | Keep your OS; add a Linux environment |
| A spare laptop or desktop | Back up its files, then install Linux |

Consider a used mini PC only when you need a separate server.

Before choosing a home server:

- **Power and noise:** check idle power use and fan noise if it will run all day.
- **RAM and storage:** check what your chosen service actually needs.
- **Networking:** prefer Ethernet for a fixed server.

**Try one service before buying any hardware.**

<!-- end_slide -->

# Ubuntu, On The Computer You Already Have

**Ubuntu LTS** builds on Debian: familiar commands and packages, with long-term support.

**WSL2:** use Linux tools inside Windows.

**VM:** run a separate Linux system, with its own desktop and boot.

| Computer | Start here |
|---|---|
| Windows: terminal work | Ubuntu with WSL2 |
| Windows: Linux desktop | Ubuntu VM with VirtualBox |
| Mac: Linux system | Ubuntu VM with UTM |

On a Mac, Terminal already supports many familiar Unix commands. macOS is not Linux; use an Ubuntu VM for Linux-specific tools and services.

<!-- end_slide -->

# Investigate, Don't Guess

Remember S8? You set up your web server. Then `guide` broke it, and you investigated.

1. **Goal:** get your page working correctly again.
2. **Observe:** inspect the service status, logs, and page response.
3. **Hypothesis:** explain what could cause that failure.
4. **Test:** repair one cause, check the page again, and compare the result.

You used `systemctl`, `journalctl`, and HTTP requests—not guesswork.

**You have already practised this. Use the same method on unfamiliar problems.**

<!-- end_slide -->

# Documentation Answers Specific Questions

**S8 question: how can I read only the recent messages for my service?**

```bash
journalctl --help
man journalctl
```

Look up `--unit` (`-u`) and `--since` to understand the command you used:

```bash
journalctl --user -u site.service --since "5 minutes ago"
```

**Start with your question, not the whole manual.**

<!-- end_slide -->

# A Small Learning Shelf

- **Course PDFs:** revisit an idea, then try it.
- **Official project docs:** install, configure, and understand your next tool.
- **[The Linux Command Line](https://linuxcommand.org/tlcl.php) — William Shotts:** free PDF, from terminal basics to Bash scripting.
- **[OverTheWire Bandit](https://overthewire.org/wargames/bandit/):** practice investigation through Linux puzzles.

**And to help you keep exploring, I have a little surprise for you at the ceremony.**

<!-- end_slide -->

# Learn With AI

When you do not know what to look for, AI can help you begin.

- **Search assistant:** discover tools, concepts, and documentation. Verify what you find.
- **Tutor:** ask how it works, why it failed, and what the fix changes.
- **Practice partner:** try a small variation and explain the result yourself.

For example: "Here is my service's error. Explain it and suggest one test before proposing a fix."

**Get the result. Keep the knowledge.**

## BUT DON'T OUTSOURCE YOUR THINKING

Sometimes, put AI aside. Read, think, investigate, and test your own ideas.

<!-- end_slide -->

# AI Helps. You Stay In Control.

Understanding a suggestion also means knowing its risks.

- Understand changes before approving them, especially with `sudo`.
- Keep passwords, tokens, and private data out of prompts.
- Use Git to save working versions and review the diff.
- Try risky system changes in a VM first.
- Don't disable the firewall or bypass HTTPS certificate checks just to make an error disappear.

**Working is not always the same as correct or safe.**

<!-- end_slide -->

# Keep Learning With People

AI is one source of help. People bring experience, feedback, and new ideas.

- Keep in touch with someone from this class.
- Meet to build something or investigate a problem.
- Show someone what you discovered. Help them try it.
- Visit a local makerspace or an in-person meetup.

**When asking for help:** share your goal, the exact error, and what you already tried.

**You can learn independently without learning alone.**

<!-- end_slide -->

# Keep Going, A Little At A Time

- Make time regularly to try one small thing.
- Before stopping, write down what you want to try next.
- Missed a week? Start again. It is not a race.

Choose a project you would enjoy using. Start with one small result.

**Small, regular experiments build your skills.**

<!-- end_slide -->

# After The Course

The classroom server will close when our cloud credits run out. No date is confirmed.

After graduation, we will email you **two archives**:

- **Your work:** a personal tarball of your existing `~/scripts`, `~/src`, and `~/playground` folders.
- **Course PDFs:** session guides, reference cards, and the home setup guide.

**Save your own copies. You can keep learning without the classroom server.**

<!-- end_slide -->

# Stay Curious. Keep Building.

Read. Try. Observe. Ask. Understand. Repeat.

There is always another approach, another explanation, another person to ask.

Thank you for learning with us.

**🎉 Congratulations. This is a beginning.**

**Now: open Q&A—ask anything you like.**

**At 3pm: graduation ceremony. Your families are welcome to join us.**
