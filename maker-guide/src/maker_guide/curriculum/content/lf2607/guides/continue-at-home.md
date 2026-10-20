# Continue at Home

Repeat the course on **Ubuntu LTS**, without a cloud account, public domain, or classroom bot.

Use the PDFs to read and the **practice ZIP** for files you would otherwise have to retype. Worked answers are separate so you can try first and compare afterward.

## 1. Open an Ubuntu environment

### Windows: WSL2

Follow [Microsoft's WSL installation guide](https://learn.microsoft.com/en-us/windows/wsl/install). On a supported computer, open **PowerShell as administrator** and run:

```powershell
wsl --install -d Ubuntu
```

Follow any restart instructions, open Ubuntu, and create its Linux account. In PowerShell, `wsl --list --verbose` should show version `2` for Ubuntu. Use an Ubuntu LTS release; `cat /etc/os-release` inside Ubuntu identifies it.

For S8–S9, run `ps -p 1` in Ubuntu. It must show systemd. If not, follow [Microsoft's systemd instructions](https://learn.microsoft.com/en-us/windows/wsl/systemd); save other WSL work before using `wsl --shutdown` to apply changes.

### Mac: Ubuntu VM

Use [UTM](https://mac.getutm.app/) and its [Ubuntu installation guide](https://docs.getutm.app/guides/ubuntu/), with an [official Ubuntu LTS image](https://ubuntu.com/download/desktop).

- Apple Silicon: ARM64/aarch64 guest.
- Intel Mac: amd64/x86-64 guest.

Use an image supported by your VM application. The UTM guide may show an older release; prefer the current LTS compatible with your setup. Open Terminal **inside Ubuntu**. For the simplest local preview, use its browser too.

### Already using Ubuntu

Open Terminal. A VM is also fine. Back up important files before installing an OS on a physical machine; disk installation can erase them.

**All remaining commands run inside Ubuntu**, not PowerShell, macOS Terminal, or classroom SSH.

## 2. Install the practice tools

On your own Ubuntu system, you may install packages:

```bash
sudo apt update
sudo apt install bash git micro curl jq caddy dnsutils iputils-ping traceroute netcat-openbsd procps iproute2 man-db manpages less file binutils xxd bzip2 unzip xz-utils
```

`sudo` asks for your Ubuntu account password; typing is invisible. These setup commands are not permission to install software on the shared classroom server.

`binutils` supplies `strings`; `xxd` supplies the hex viewer. Cards for optional tools such as tmux, htop, bat, tree, and Vim require those tools separately; the core exercises do not require installing every reference-card tool.

Check the user manager before S8–S9:

```bash
systemctl --user status
```

Press `q` to leave a pager. If it cannot connect to the user bus, resolve your Ubuntu login/systemd setup before attempting service exercises. Do not replace `--user` with `sudo` to hide the error.

## 3. Install Node for the site

The kit reuses the course's Astro site builder. It needs **Node 24 LTS** and npm; Ubuntu's default `nodejs` package may be too old.

At [Node's official download page](https://nodejs.org/en/download), choose the Node 24 LTS Linux binary archive (`.tar.xz`). In Ubuntu, `uname -m` identifies your processor: `x86_64` needs `linux-x64`; `aarch64` needs `linux-arm64`. Follow the official checksum-verification instructions before extracting.

For a stable installation usable by systemd, put the archive's contents in `~/.local/node`. If that directory already exists, inspect the existing installation instead of overwriting it.

```bash
mkdir -p ~/.local
mkdir ~/.local/node
```

Only after the second command succeeds, extract your downloaded archive. Replace the example filename with the actual version and architecture you downloaded:

```bash
tar -xJf ~/Downloads/node-v24.X.Y-linux-x64.tar.xz --strip-components=1 -C ~/.local/node
export PATH="$HOME/.local/node/bin:$PATH"
node --version
npm --version
```

The first result should begin `v24.`. If Windows downloaded the file, either download it inside Ubuntu or use its actual `/mnt/c/Users/.../Downloads/` path.

Use `micro ~/.bashrc` to add `export PATH="$HOME/.local/node/bin:$PATH"` once, so future Bash terminals find Node. Systemd does not read `.bashrc`; S9 specifies the executable and PATH separately.

## 4. Unpack the files

Download or copy `linux-foundations-practice.zip` into Ubuntu. If `~/linux-foundations-practice` already exists, keep it and extract the new ZIP elsewhere for comparison.

```bash
unzip ~/Downloads/linux-foundations-practice.zip -d ~
```

The kit contains:

| Directory | Contents |
|---|---|
| `site/` | Local Astro starter, without class progress or tokens |
| `starters/` | Exercises to finish yourself |
| `answers/` | Complete example scripts; compare after trying |
| `reading/` | Markdown copies and reference cards, for searching |

The PDF bundle contains the home guide, ten session guides, worked answers, and reference cards. Keep the PDF directory structure intact so links between files work. There are no purchased zine PDFs.

## 5. Build your local site

These exercises use `~/src` and publish to `~/public_html`. The builder replaces published output after a successful build, so **do not use these locations for an unrelated project**.

Inspect them first:

```bash
ls -ld ~/src ~/public_html ~/.public_html-previous
```

Missing paths are expected on a fresh account. If these contain unrelated work, use a separate Ubuntu account for the course instead of merging or deleting it. The builder uses `.public_html-previous` as a temporary recovery directory; inspect any existing recovery copy before rebuilding. If `~/src` is your existing course project, back it up and compare it with the kit before making changes.

For a fresh setup only:

```bash
cp -r ~/linux-foundations-practice/site ~/src
cd ~/src
npm ci
node scripts/build.mjs
ls -l ~/public_html/index.html
```

`npm ci` downloads the locked dependencies. Later builds reuse them. A failed download/build is an error to investigate, not permission to delete your source.

The source is still Markdown in `~/src/pages`. The kit uses a local layout and omits the classroom-only Codex PDF step; it does not install or contact the class bot.

To publish later edits:

```bash
cd ~/src
node scripts/build.mjs
```

This is the home equivalent of `build-website`. It works independently of your current prompt after you change to the project directory.

## 6. Preview locally

In one Ubuntu terminal:

```bash
caddy file-server --listen 127.0.0.1:8080 --root "$HOME/public_html" --access-log
```

Leave it running and open **http://localhost:8080/**. With WSL2, a Windows browser normally reaches this address through localhost forwarding. If not, check Microsoft's WSL networking guidance. In a VM, start with the Ubuntu browser; host access is a separate networking exercise.

This server listens only on loopback. Do not open firewall/router ports. Press `Ctrl-C` in its terminal to stop it before S7 or S8 starts another server on that port.

For S6:

```bash
export BASE_URL="http://localhost:8080"
```

Export it in the terminal running the checker. Its report-repair message should use the local build command, not `build-website`.

## What changes outside class?

| Classroom feature | Home equivalent |
|---|---|
| SSH login | Ubuntu terminal; SSH becomes an optional remote-machine exercise |
| `/docs` | PDFs and the kit's `reading` directory |
| `build-website` | `cd ~/src && node scripts/build.mjs` |
| Public static/service URLs | `http://localhost:8080/` |
| UID-based port | Local port `8080`, bound to `127.0.0.1` |
| Forgejo/token | Local Git; configure your own remote only if wanted |
| `guide` checks and injected faults | Observations, worked answers, and manual S8 experiments |
| Public HTTPS reverse proxy | Classroom extension; not needed for local practice |

Services and timers cannot run while their Linux environment is stopped. WSL/VM shutdown is different from closing one terminal. Do not expect a local service to stay online when your laptop is asleep or off.

## Your next step

Start with the session you want to revisit. Read a short section, predict the result, run the example, then compare with [Worked Answers](self-study-answers.md). Preserve your own changes rather than resetting files merely to match the guide.
