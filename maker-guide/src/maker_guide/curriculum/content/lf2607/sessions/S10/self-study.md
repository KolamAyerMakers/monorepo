# S10: Keep Learning Forever

Session: S10

2026-10-24

This is a starting guide for after the course, not another assignment. Choose an environment, a project, and one useful resource. You do not need to do everything here.

## Keep Your Work

The classroom server and SSH accounts will close shortly after graduation. The follow-up email will confirm the date and include your scripts, useful files from your playground, and the course PDFs. You do not need to learn archive or transfer commands during the final session.

The printed *At the Prompt* anthology is your reading and experimenting companion. The email contains course PDFs, not copies of the purchased Julia Evans zines.

## Choose Your Next Linux

We used Debian in the classroom. **Ubuntu LTS** is a practical next step: it builds on Debian, uses familiar package tools, and offers a desktop. Pick an environment before spending time comparing distributions.

### Windows: Start With WSL2

WSL2 runs Linux alongside Windows. It is useful for Bash, scripts, programming, packages, and many services. It is not just a simulated terminal, but it does not give you the same independent desktop and boot experience as a full VM.

Follow [Microsoft's WSL installation guide](https://learn.microsoft.com/en-us/windows/wsl/install). Check Windows compatibility, administrator access, and virtualization support first. On a supported machine, the basic installation is:

```powershell
wsl --install
```

Run that in **Windows PowerShell as administrator**, not in classroom SSH or a Linux shell. Follow the restart instructions, open Ubuntu, and create your Linux account. Check the installed version from PowerShell:

```powershell
wsl --list --verbose
```

Your Ubuntu entry should show version `2`. If installation fails, use the error and the official troubleshooting guide rather than repeatedly guessing commands.

### Windows: A Full Linux VM

For a Linux desktop, independent boot, and a machine you can experiment with, use a VM. A virtual machine runs a guest operating system inside your existing computer without replacing Windows.

Use a virtualization application compatible with your hardware; [VirtualBox's manual](https://www.virtualbox.org/manual/) is one starting point for supported Windows hosts. Follow its installation instructions and use an [official Ubuntu LTS image](https://ubuntu.com/download). Match the guest image to the supported processor architecture, leave memory and disk space for Windows, and take a VM snapshot before risky experiments. WSL2 and VM applications can interact with Windows virtualization features; consult their current compatibility guidance if performance or startup is poor.

### Mac: Ubuntu In UTM

Use [UTM for macOS](https://mac.getutm.app/) and its [Ubuntu guide](https://docs.getutm.app/guides/ubuntu/). Check your chip in **About This Mac**:

- Apple Silicon (M-series): use an **ARM64/aarch64** image.
- Intel: use an **amd64/x86-64** image.

Virtualizing the matching architecture is different from emulating another processor. Follow the current UTM guide and Ubuntu download information; the guide's example release may be older than the current LTS. If it uses Ubuntu Server, it starts without a graphical desktop and explains how to add one.

The macOS terminal is useful, but macOS is not Linux. Commands and options can differ, and classroom systemd services need a Linux environment.

### A Machine You Can Dedicate

An old PC can become an Ubuntu machine or home server. A Raspberry Pi with Raspberry Pi OS can run small services and connect to sensors. Use the [Ubuntu installation guide](https://ubuntu.com/tutorials/install-ubuntu-desktop) or [Raspberry Pi's getting-started guide](https://www.raspberrypi.com/documentation/computers/getting-started.html).

Back up anything you need before installing an operating system. Disk installation or imaging can erase files. Dual boot is possible, but is not required to continue learning; a VM is a simpler first experiment on your only computer.

### Optional: Omarchy

[Omarchy](https://omarchy.org/) combines Arch Linux, Hyprland, a keyboard-driven desktop, and integrated development and AI tools. It is an adventurous alternative for people who want to reshape their working environment, not another prerequisite.

Use its current official installation and try-in-a-VM instructions for your hardware. Do not assume an image or installer works on every PC or Mac. Keep a working environment and backups. AI can help change a configuration, understand an error, or create a shortcut; understand the change, test it, and know how to undo it. Paid AI services are optional tools, not a requirement for this learning path.

## Your First Small Experiment

Once you have a Linux shell on your own machine, use a scratch directory:

```bash
mkdir -p ~/playground/learning
cd ~/playground/learning
printf '%s\n' '$HOME'
printf '%s\n' "$HOME"
```

Before running the last two commands, predict whether they will print the same thing. Compare the result. Read about quoting in *Bite Size Bash* or your course notes. Change the example and predict again.

That is a complete learning session: **a question, a prediction, an experiment, and an explanation**. You do not need a large project to practice.

## When You Get Stuck

1. State the intended result and what actually happened.
2. Read the complete error. Look for a path, an option, a permission, or a connection that failed.
3. Form one hypothesis. Choose one small test.
4. Observe the result before changing anything else.
5. Keep what worked; revise what did not. Ask for help when you need it.

Repeating an unchanged failed command is not the same as investigating. Reduce the example, read the relevant documentation, inspect the code if it helps, or take a break. Before stopping, leave yourself the next thing to test so restarting is easy.

### Read Documentation With A Question

```bash
ls --help
man ls
```

Use help for a quick overview and the manual for details. In the usual manual pager, `/sort` searches for `sort`, `n` finds the next match, and `q` exits. Start with the description and the option you need; you do not need to read every option. A minimal Linux installation may need its manual packages installed before `man` is available.

For a project, prefer its current official documentation for your version. Read the prerequisites and distinguish instructions for your computer from those for a server. Try examples in your playground, not on your only copy of important files.

### Use AI As An Investigation Partner

Give your goal, system, exact error, and observations. For example:

> Chrome has no sound, but other apps do. I am using Linux and do not understand its audio system. Help me investigate. What should I check first, and what would the result tell us?

Ask for explanations, tests, or a procedure. Feed back the real result rather than saying only "it doesn't work." AI can introduce tools and concepts you have never used, but it can also guess incorrectly.

Before approving a change, understand what it does and how to undo it. Be especially careful with `sudo`, disk operations, deletion, and network security. Do not share passwords, tokens, private keys, or other people's personal data. Redact them from logs too.

For Wi-Fi authentication, use the provider's official settings and certificate requirements; do not disable certificate verification to bypass a connection problem. For cameras, investigate only equipment you own or are authorized to manage, change default passwords, and keep access local until you understand secure remote access.

### Ask People Too

Use a project's official support community, a relevant forum, or a local makerspace. Search for the exact error first. A useful question includes:

- Your goal and operating system/application version.
- The command or configuration, with secrets removed.
- The exact error and what you already tested.
- The observation you do not understand.

Explain what eventually solved it so someone else can learn from your investigation. The instructor may be able to answer an occasional specific question by email, but your learning should not depend on one person's availability.

## Build Something You Want To Use

### A Homelab That Grows With You

A homelab is your own place to run services and experiment. Start in a VM if you have one computer; an old PC or a Raspberry Pi can become a dedicated machine if you already have one. You do not need to buy equipment before starting.

One possible progression:

1. Follow [Jellyfin's official documentation](https://jellyfin.org/docs/) to install it on a supported system. Add one video you own or have permission to use.
2. Play it on the host, then on another device on your home network. Learn which address and port to use. If a VM cannot be reached, investigate its network mode instead of opening your router to the Internet.
3. Locate the service, configuration, media files, and logs. Explain what they do. Storage, media formats, and hardware affect playback; a small Pi may not handle demanding video transcoding.
4. Back up something useful and test restoring it. A backup you have never restored is an untested plan.
5. Add one more service because you want to use it, not because a diagram looks impressive.

Possible directions—not a checklist:

| Interest | First result | One next improvement |
|---|---|---|
| Media | Play one video with Jellyfin | Add a second device and investigate playback |
| Retro gaming | Run a homebrew game with [RetroArch](https://www.retroarch.com/) | Configure a controller; learn the host's supported setup |
| Video surveillance | View your own camera locally | Learn its stream/protocol and record to local storage |
| A game server | Run a small server and join on your LAN | Invite a friend; understand access before exposing it |
| Home automation | Read a sensor with [Home Assistant](https://www.home-assistant.io/getting-started/) | Make one useful automation |
| Photos | Import a small copied sample into [Immich](https://immich.app/docs/) | Test backup and restore before trusting it with originals |

Use legal game/media sources. Keep cameras and other services off the public Internet at first. Adding containers, monitoring, secure remote access, or multiple machines can come later when you have a reason to learn them.

### Other Paths

- **Data:** choose an API about a game, sport, or subject you follow. Save one response and produce a small useful report. Check the API's terms, limits, and units.
- **Programming:** use the [official Python tutorial](https://docs.python.org/3/tutorial/) to explore turning a shell script into a small tool. Start with one input and one result, not an entire application.
- **Your environment:** make one keyboard shortcut or small command that removes an annoyance. Try AI-assisted customization on a copy or a VM snapshot first.
- **Security puzzles:** [OverTheWire Bandit](https://overthewire.org/wargames/bandit/) gives you authorized Linux challenges. Read the current connection instructions, start at level 0, and investigate one question at a time. No score or completion target is required.

For employment, a small project you can explain is useful evidence: its purpose, how it works, one real failure, and how you verified a repair. A copied project you cannot explain is not the same evidence, and no project guarantees a job.

## A Small Learning Shelf

Start with **At the Prompt**, the printed anthology of five Julia Evans zines. Use it according to your question, not a required reading order:

| Zine | Reach for it when… |
|---|---|
| The Secret Rules of the Terminal | Terminal behavior surprises you |
| Bite Size Command Line | You want to try a tool or combine commands |
| Bite Size Linux | You want to understand what the system is doing |
| Bite Size Bash | You are building a script or investigating shell behavior |
| How Git Works | You want to understand changes and versions in a project |

Read one page, predict what an example will do, try a small experiment, and change something. You can return to difficult pages when your project gives you a reason.

Keep just a few extra resources nearby:

- [Julia Evans's blog](https://jvns.ca/) and [Wizard Zines experiments](https://wizardzines.com/#experiments): approachable explanations and small playgrounds. [Mess with DNS](https://messwithdns.net/) lets you experiment without changing your real domain.
- Your course PDFs and the official docs for the project you are currently building.
- Bandit when you want a puzzle, not another obligation.

Choose one next result small enough to finish, and a time that fits your life. Ten focused minutes count. If you stop for a week, return to the next small test—not to guilt about an unfinished plan.

**Start small. Make it work. Use it. Understand it. Improve it. KEEP LEARNING FOREVER.**
