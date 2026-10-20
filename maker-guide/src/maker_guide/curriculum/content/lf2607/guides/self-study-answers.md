# Worked Answers — Linux Foundations

Try the exercise first. Use these answers to compare your reasoning, not to match every character of output. Usernames, paths, PIDs, dates, forecasts, and log formatting vary.

The practice kit includes complete scripts in `answers/`. Read and compare before copying; keep your own working version. The references are examples, not the only correct implementations.

## S1: First Contact

1. After SSH login, `hostname` runs on the **remote server**. Your terminal still displays its output locally.
2. From `/etc`, `cd ..` goes to `/`.
3. `cat` prints all contents; `head` prints the beginning; `less` lets you browse without dumping the whole file.
4. `ls -S` sorts by file size, largest first. The manual confirms the option; it is not alphabetical sorting.

An absolute path begins at `/`. A relative path is interpreted from your current directory. `pwd` helps distinguish them. A returning prompt means the command has finished, not necessarily succeeded.

## S2: Files and Keys

Expected practice files:

- `one.txt`, `two.txt`, `three.txt`: empty unless you deliberately edited them.
- `micro-note.txt`: `edited with micro`.
- `hi.txt`: `hello makers`, then `again`, on separate lines.
- `overwrite-demo.txt`: only `replacement`.

`one.txt` survives because you removed its **copy**, not the original. A removed empty practice directory is gone; no recursive deletion is needed.

The public key may be copied to the server. The private key must remain on your own computer. Overwriting it can destroy access to other machines using that key. A passphrase prompt protects that file; an account-password prompt authenticates to the server.

The website changes only after source is saved and successfully built. Rebuilding replaces generated HTML, which is why direct output edits do not last.

## S3: Streams, Pipes, and Processes

1. The valid `ls` result goes to stdout (`1`); the missing-path diagnostic goes to stderr (`2`). Both normally reach the terminal, but can be redirected independently.
2. `>file 2>&1` combines them in the file. `2>&1 >file` leaves stderr at stdout's **previous** destination, usually the terminal, and sends only stdout to the file.
3. `uniq -c` groups only adjacent equal lines; sorting makes equal shell values adjacent.
4. `tee` saves a copy while forwarding the same stream to the next command.
5. A PID identifies a running process. The same executable file may be used by several processes with different PIDs.

`wc -l` counts newline characters. A missing final newline can make its count differ from your visual line count. Local `/etc/passwd` is not necessarily the complete account directory of a networked machine.

## S4: Permissions and Git

Directory `x` permits traversal; `r` lists names. Without traversal permission, seeing a name does not mean you can enter or open it. Owning a directory does not bypass its permission bits during normal access, though the owner can restore them with `chmod`.

Git's states:

| State | Where it is |
|---|---|
| Working change | Your editable files |
| Staged change | Index: selected for the next commit |
| Committed snapshot | Local repository history |
| Pushed commit | Also present at a remote repository |

Inspect with `git diff`, `git diff --cached`, and `git log --oneline`. A clean status does not mean the remote has your commits.

Ignoring `scratch.tmp` hides it from normal untracked status; it does not delete the file. `.gitignore` does not stop tracking a file already committed.

## S5: Shell Scripts

1. `bash file` opens readable script text. Direct execution needs execute permission; the shebang selects Bash.
2. The shebang must be the first line.
3. Caller quotes keep the title in one argument. Expansion quotes keep that value in one argument when another command uses it.
4. The grouped redirection sends stdout to Markdown. Stderr stays on the terminal.
5. The browser receives HTML, not the newly generated Markdown. A build renders and publishes it.

### Safer supplied report

The kit's `answers/maker-report.sh` produces the same report, but checks that exactly one title was supplied and writes to a temporary file beside the destination. Only after generation succeeds does it replace `maker-report.md`.

This avoids truncating the last good report before discovering a failure. Its trap removes the temporary file when the script exits. `set -euo pipefail` is a useful backstop here, not a universal error handler; S6 handles expected curl failures explicitly.

Run without overwriting your own script:

```bash
bash ~/linux-foundations-practice/answers/maker-report.sh "Reference Report"
cat ~/src/pages/maker-report.md
```

This **does** replace the generated Markdown on success; keep handwritten notes elsewhere.

## S6: Site Checker

DNS asks which records a name has. Ping asks whether ICMP echo replies arrive. Curl's exit code says whether its transfer succeeded. HTTP status describes the server's response. These results are related, not interchangeable.

`""` is one argument containing an empty string; the script appends `/` and checks the homepage. Zero arguments run no loop iterations, so a guard prints usage and exits `2`.

`for page in "$@"` visits the supplied arguments in order. `if` chooses a diagnosis for each. Keep transport failure separate from HTTP—even a printed `200` must not override curl's nonzero exit code.

| Case | Expected message/advice |
|---|---|
| Curl succeeds, HTTP `200` | `OK`, with the requested URL |
| Report `404` | `MISSING`; generate report, then build |
| Another page `404` | `CHECK`, its code and URL; inspect headers |
| `302` or `500` | `CHECK`, actual code; no false report-repair advice |
| Curl exits `6` | Connection failure; read the name-resolution diagnostic |
| Curl exits `28`, even with `200` printed | Connection failure; inspect timeout/partial-transfer error |

The kit's `answers/site-check.sh` is extracted from the guide, with local build advice. At home:

```bash
export BASE_URL="http://localhost:8080"
bash ~/linux-foundations-practice/answers/site-check.sh "" maker-report.html
```

The checker deliberately prints diagnoses rather than summarizing health in its process exit code. A `HEAD 200` still needs a content check: retrieve the body and inspect the browser page.

## S7: Web Server

Your `ps` row names the process, arguments, and PID. `ss` connects that PID to the listener. Curl and the log show an actual request and response.

HTTP/1.1 lines end in CRLF (`\r\n`). The empty line ends the headers. In the script, the final empty `printf` argument supplies that line; EOF from the pipe only closes sending. It is not HTTP syntax.

| Failure | Process/listener | Local result | Classroom proxy result |
|---|---|---|---|
| Empty root | Present | HTTP `404` | Usually `404` from the backend |
| Stopped backend | Absent | Refusal; no HTTP response | `502` from shared Caddy, if the public route works |

The static classroom URL survives because shared Caddy reads the real published files without your backend. A `502` alone does not prove your process stopped; the local process/socket observations narrow the cause.

## S8: systemd

| Command | Purpose |
|---|---|
| `verify` | Check saved unit instructions, not application behaviour |
| `daemon-reload` | Reread saved units |
| `start` | Start an inactive service now |
| `restart` | Stop/start using the loaded instructions |
| `enable` | Arrange startup with the relevant manager/target |

`Ctrl-C` on `journalctl -f` stops the reader, not the service. Restarting Caddy cannot regenerate a missing HTML file; building can.

### Five home experiments

Do these only on your **local course service**, never a shared server. Start from a working page, preserve your installed unit, and run one experiment at a time.

Create a private working directory and backup in the terminal you will keep using:

```bash
lab=$(mktemp -d)
chmod 700 "$lab"
cp ~/.config/systemd/user/site.service "$lab/site.service"
```

If creation or copying fails, stop before changing anything. Keep `$lab` available; do not close this terminal until restoration is complete.

For each unit experiment: edit, run `daemon-reload`, restart, inspect status and the journal, then try local curl. Unit verification is another useful observation; do not treat a deliberately faulty unit as ready for normal use.

#### Experiment 1: missing executable

**Try:** change only `/usr/bin/caddy` in `ExecStart` to `/usr/bin/cadddyyy`.

**Look for:** verification of the missing path and journal `203/EXEC`. Caddy never started. Restore the executable path.

#### Experiment 2: invalid argument

**Try:** change only `--access-log` to `--access-logs`.

**Look for:** Caddy's “unknown flag” diagnostic. The executable launched but rejected its arguments. Unit verification cannot validate Caddy's options. Restore the flag.

#### Experiment 3: wrong root

**Try:** create `mkdir "$lab/empty"`, then replace only the unit's root with that directory's actual absolute path. Keep your working directory unchanged.

**Look for:** active process, listener, and `404` response. The service is running but serving no index. Restore `%h/public_html`; do not add directory browsing.

#### Experiment 4: wrong homepage

**Try:** with the service using the correct root, preserve the generated index, then replace only that generated page:

```bash
cp ~/public_html/index.html "$lab/index.html" && printf '<h1>Wrong homepage</h1>\n' > ~/public_html/index.html
```

`&&` prevents replacement if the backup fails. Stop on any error; otherwise reload the browser and request it with curl.

**Look for:** HTTP `200` with wrong content. Status alone is insufficient. Rebuild from your unchanged Markdown source to restore the real homepage; no service restart is needed.

#### Experiment 5: missing publication

**Try:** first confirm that `~/src/pages/index.md` still exists and your previous repair is complete. Move your course output into the private lab directory:

```bash
mv -Ti ~/public_html "$lab/public_html"
```

**Look for:** Caddy can remain active while requests return `404`. It cannot serve files that are absent.

**Repair:** `cd ~/src && node scripts/build.mjs`. If the build fails, retain the error and restore the backup only while `~/public_html` is absent: `mv -i "$lab/public_html" ~/public_html`. Do not merge an existing output tree blindly.

### Restore after every experiment

If you are unsure what changed, restore the backed-up unit, then:

```bash
cp -i "$lab/site.service" ~/.config/systemd/user/site.service
systemd-analyze --user verify ~/.config/systemd/user/site.service
systemctl --user daemon-reload
systemctl --user reset-failed site.service
systemctl --user restart site.service
curl -i --max-time 10 http://127.0.0.1:8080/
```

Inspect the browser too. Do not begin the next fault until your correct homepage works. Keep the backup directory until finished; it is private and does not need recursive cleanup as part of this lesson.

## S9: Bulletin and Timer

`.daily.temperature_2m_max[0]` selects the first element in the named array. A misspelled/missing selector often produces `null`; successful JSON parsing alone does not prove usable data.

The complete, checked generator is `answers/today.sh` in the kit, or `guides/resources/today.sh` in the course files. It:

1. Downloads into a fresh private temporary directory.
2. Uses `jq -e` and type checks to reject absent or unusable fields.
3. Writes the complete bulletin to a temporary file beside its destination.
4. Replaces `today.md` only after successful collection and formatting.

Forecast/model times are unchanged Singapore-time strings; retrieval time comes from `date` and includes your machine's timezone. PM2.5 is explicitly modelled and attributed, not presented as official PSI.

To install this example **after comparing with your own work**:

```bash
cp -i ~/linux-foundations-practice/answers/today.sh ~/scripts/today.sh
bash ~/scripts/today.sh
cat ~/src/pages/today.md
```

Then build and inspect both pages. Do not schedule a generator until its manual run works.

With the Node installation in the home guide, the local build service is:

```ini
[Unit]
Description=Generate and publish my bulletin

[Service]
Type=oneshot
WorkingDirectory=%h/src
Environment=PATH=%h/.local/node/bin:/usr/local/bin:/usr/bin:/bin
ExecStartPre=/bin/bash %h/scripts/today.sh
ExecStart=%h/.local/node/bin/node %h/src/scripts/build.mjs
```

`Environment` supports `%h` here; it is not shell `$HOME` expansion. If you installed Node elsewhere, use its actual permanent directory and executable.

The S9 timer starts this matching service. `ExecStartPre` generates before `ExecStart` publishes. A failed generator prevents that build, preserving the last published bulletin.

An inactive completed oneshot is normal. An active timer may simply be waiting. Confirm a real scheduled execution using journal timestamps and the page's retrieval time—not only its next deadline. Disable the timer when finished.

## S10: Keep Learning

Single quotes in `'$HOME'` preserve literal text, so the first command prints `$HOME`. Double quotes allow variable expansion while preserving one argument, so the second prints your home path.

A useful next experiment: compare `printf '%s\n' "$HOME"` with `printf '%s\n' "${HOME}/playground"`. Predict the result before running it.
