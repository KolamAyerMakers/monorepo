# S10 Self-Study Guide: Boss Fight And Graduation

Session: S10

## Study Path

1. Start Bandit with a written note file, not memory.
2. Read the official level goal before each level.
3. Use `file` before choosing a decoder.
4. Use scratch directories before extracting archives.
5. Demo your site with commands, not claims.
6. Publish `next.md` with one concrete Linux path after graduation.

## Bandit Start

```bash
ssh bandit0@bandit.labs.overthewire.org -p 2220
```

Read [OverTheWire Bandit](https://overthewire.org/wargames/bandit/) before each level. Password input is invisible at SSH prompts; that is normal.

## Unknown File Workflow

```bash
mkdir -p ~/bandit-work
cp suspicious-file ~/bandit-work/
cd ~/bandit-work
file suspicious-file
strings suspicious-file | less
xxd suspicious-file | head
```

Archive workflow:

```bash
mkdir -p extract
tar -tf archive.tar
tar -xf archive.tar -C extract
```

Compression workflow:

```bash
file data
bzip2 -d data.bz2
base64 -d encoded.txt
```

## Stuck Table

- `Permission denied`: check username, host, port, and password.
- Password paste shows nothing: normal SSH behavior.
- `No such file`: run `pwd` and `ls -la`.
- Output is huge: pipe to `less`, `head`, or `grep`.
- File looks binary: run `file`, then `strings`, then `xxd`.
- Archive creates many files: extract in a scratch directory.

## Demo Script

```bash
curl -I https://lf2607.kolamayermakers.org/~username/
git -C ~/src log --oneline -5
git -C ~/src status
systemctl --user status site.service
journalctl --user -u site.service --no-pager -n 20
```

Show the public site, Forgejo repo, README, last commit, service status, and one failure you recovered from.

## Next Path Template

```text
Path: Bandit / homelab / laptop / cloud server / club project
First action:
Date:
Risk:
Recovery plan:
Documentation I will use:
Proof I completed it:
```

## Proof Checklist

- You solved one Bandit level and can name the command that mattered.
- Your public site and source repo are reachable.
- Your service status and logs are explainable.
- `next.md` names one real next action and one documentation source.

## Docs Pointers

- [OverTheWire Bandit](https://overthewire.org/wargames/bandit/)
- [Debian Handbook](https://www.debian.org/doc/manuals/debian-handbook/)
- [Ubuntu Server documentation](https://documentation.ubuntu.com/server/)
- [Arch Wiki](https://wiki.archlinux.org/) as reference material, not a beginner install prescription.
- Read [file compression](../../concepts/file-compression.md) before extracting archives.
- Read [file encoding](../../concepts/file-encoding.md) and [number bases](../../concepts/number-bases.md) before using `xxd` heavily or assuming a file is plain text.
